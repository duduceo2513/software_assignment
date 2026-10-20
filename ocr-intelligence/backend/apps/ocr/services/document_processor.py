"""Turns an uploaded PDF / PNG / JPEG / TIFF into a sequence of page images on disk."""
import logging
from collections.abc import Iterator
from pathlib import Path

import pymupdf
from django.conf import settings
from PIL import Image, ImageOps, ImageSequence

logger = logging.getLogger(__name__)

PDF_MIME = "application/pdf"


def iter_page_images(source: Path, mime_type: str, work_dir: Path) -> Iterator[tuple[int, Path]]:
    """Yield (page_number starting at 1, PNG path) lazily so only one page is rendered at a time."""
    work_dir.mkdir(parents=True, exist_ok=True)
    if mime_type == PDF_MIME:
        yield from _iter_pdf(source, work_dir)
    else:
        yield from _iter_image(source, work_dir)


def _iter_pdf(source: Path, work_dir: Path) -> Iterator[tuple[int, Path]]:
    zoom = settings.OCR_PDF_RENDER_DPI / 72
    with pymupdf.open(source) as pdf:
        for index, page in enumerate(pdf, start=1):
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
            target = work_dir / f"page-{index:04d}.png"
            pixmap.save(target)
            yield index, target


def _iter_image(source: Path, work_dir: Path) -> Iterator[tuple[int, Path]]:
    with Image.open(source) as image:
        for index, frame in enumerate(ImageSequence.Iterator(image), start=1):
            prepared = ImageOps.exif_transpose(frame).convert("RGB")
            target = work_dir / f"page-{index:04d}.png"
            prepared.save(target, format="PNG")
            yield index, target
