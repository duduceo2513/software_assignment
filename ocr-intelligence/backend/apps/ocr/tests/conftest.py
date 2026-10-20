import io

import pymupdf
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, ImageDraw
from rest_framework.test import APIClient

from apps.ocr.services import ocr_engine
from apps.ocr.services.ocr_engine import Block


@pytest.fixture(autouse=True)
def isolated_media(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path / "media")


@pytest.fixture
def client():
    return APIClient()


def make_png(size=(200, 120), text="OCR") -> bytes:
    image = Image.new("RGB", size, "white")
    ImageDraw.Draw(image).text((10, 10), text, fill="black")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def make_tiff(pages=2) -> bytes:
    frames = [Image.new("RGB", (100, 100), "white") for _ in range(pages)]
    buffer = io.BytesIO()
    frames[0].save(buffer, format="TIFF", save_all=True, append_images=frames[1:])
    return buffer.getvalue()


def make_pdf(pages=2) -> bytes:
    pdf = pymupdf.open()
    for number in range(pages):
        page = pdf.new_page()
        page.insert_text((72, 72), f"Page {number + 1}")
    data = pdf.tobytes()
    pdf.close()
    return data


@pytest.fixture
def png_file():
    return SimpleUploadedFile("scan.png", make_png(), content_type="image/png")


@pytest.fixture
def pdf_file():
    return SimpleUploadedFile("report.pdf", make_pdf(2), content_type="application/pdf")


class FakeEngine:
    """Deterministic stand-in used only by unit tests; the running app uses PaddleOCR."""

    def __init__(self, fail_on: str | None = None):
        self.calls = 0
        self.fail_on = fail_on

    def recognize_page(self, image_path, language):
        self.calls += 1
        if self.fail_on and self.fail_on in str(image_path):
            raise RuntimeError("boom")
        return [
            Block("doc_title", "Қазақстан Республикасы"),
            Block("text", f"Привет, мир! ӘҒҚҢӨҰҮҺІ ({language}) page {self.calls}"),
            Block("table", "", table_html="<table><tr><td>A</td><td>B</td></tr><tr><td>1</td><td>2</td></tr></table>"),
        ]


@pytest.fixture
def fake_engine(monkeypatch):
    engine = FakeEngine()
    monkeypatch.setattr(ocr_engine, "get_engine", lambda: engine)
    return engine
