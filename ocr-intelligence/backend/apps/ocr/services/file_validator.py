"""Upload validation: size, extension, magic bytes, and a structural parse of the content."""
import io
import re
import unicodedata
from dataclasses import dataclass
from pathlib import PurePath

import pymupdf
from django.conf import settings
from PIL import Image, UnidentifiedImageError


class FileValidationError(ValueError):
    """Raised with a user-facing message when an upload is rejected."""


@dataclass(frozen=True)
class ValidatedFile:
    filename: str
    mime_type: str
    extension: str
    size: int
    page_count: int


# extension -> (canonical mime, kind)
ALLOWED_TYPES = {
    ".pdf": ("application/pdf", "pdf"),
    ".png": ("image/png", "image"),
    ".jpg": ("image/jpeg", "image"),
    ".jpeg": ("image/jpeg", "image"),
    ".tif": ("image/tiff", "image"),
    ".tiff": ("image/tiff", "image"),
}

_SIGNATURES = {
    "application/pdf": (b"%PDF-",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/tiff": (b"II*\x00", b"MM\x00*"),
}


def sanitize_filename(raw: str) -> str:
    """Drop directories, control characters and odd symbols; keep unicode letters (Cyrillic names)."""
    name = PurePath(raw.replace("\\", "/")).name
    name = unicodedata.normalize("NFC", name)
    name = "".join(ch for ch in name if ch.isprintable())
    name = re.sub(r"[<>:\"|?*\x00-\x1f]", "_", name).strip(" .")
    if len(name) > 150:
        stem, dot, ext = name.rpartition(".")
        name = (stem[: 150 - len(ext) - 1] + dot + ext) if dot else name[:150]
    return name or "document"


def detect_mime(head: bytes) -> str | None:
    for mime, signatures in _SIGNATURES.items():
        if any(head.startswith(sig) for sig in signatures):
            return mime
    return None


def validate_upload(uploaded_file) -> ValidatedFile:
    filename = sanitize_filename(getattr(uploaded_file, "name", "") or "")
    extension = PurePath(filename).suffix.lower()
    if extension not in ALLOWED_TYPES:
        raise FileValidationError(
            f"'{filename}': unsupported format. Allowed: PDF, PNG, JPG/JPEG, TIFF."
        )

    max_bytes = settings.OCR_MAX_FILE_SIZE_MB * 1024 * 1024
    size = uploaded_file.size
    if size == 0:
        raise FileValidationError(f"'{filename}': the file is empty.")
    if size > max_bytes:
        raise FileValidationError(f"'{filename}': file is larger than {settings.OCR_MAX_FILE_SIZE_MB} MB.")

    uploaded_file.seek(0)
    data = uploaded_file.read()
    uploaded_file.seek(0)

    declared_mime, kind = ALLOWED_TYPES[extension]
    sniffed = detect_mime(data[:16])
    if sniffed != declared_mime:
        raise FileValidationError(f"'{filename}': file content does not match the '{extension}' extension.")

    page_count = _count_pdf_pages(data, filename) if kind == "pdf" else _count_image_pages(data, filename)
    if page_count < 1:
        raise FileValidationError(f"'{filename}': the document has no pages.")
    if page_count > settings.OCR_MAX_PAGES_PER_DOCUMENT:
        raise FileValidationError(
            f"'{filename}': {page_count} pages exceeds the limit of {settings.OCR_MAX_PAGES_PER_DOCUMENT}."
        )
    return ValidatedFile(filename, declared_mime, extension, size, page_count)


def _count_pdf_pages(data: bytes, filename: str) -> int:
    try:
        with pymupdf.open(stream=data, filetype="pdf") as pdf:
            if pdf.needs_pass or pdf.is_encrypted:
                raise FileValidationError(f"'{filename}': password-protected PDFs are not supported.")
            return pdf.page_count
    except FileValidationError:
        raise
    except Exception as exc:  # noqa: BLE001 - PyMuPDF raises several unrelated types
        raise FileValidationError(f"'{filename}': the PDF is corrupted or unreadable.") from exc


def _count_image_pages(data: bytes, filename: str) -> int:
    try:
        with Image.open(io.BytesIO(data)) as image:
            width, height = image.size
            frames = getattr(image, "n_frames", 1)
            if width * height > settings.OCR_MAX_IMAGE_PIXELS:
                raise FileValidationError(f"'{filename}': image resolution is too large.")
            image.verify()
            return frames
    except FileValidationError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError, ValueError) as exc:
        raise FileValidationError(f"'{filename}': the image is corrupted or unreadable.") from exc
