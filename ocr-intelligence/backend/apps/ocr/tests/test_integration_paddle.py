"""Real PaddleOCR run. Deselected by default; run with:  pytest -m integration -o addopts=""
Requires requirements-ocr.txt (Python <= 3.13) and downloads model weights on first use."""
import io

import pytest
from django.test import override_settings
from PIL import Image, ImageDraw, ImageFont

pytestmark = pytest.mark.integration


def _render(text: str) -> bytes:
    font = None
    for candidate in ("DejaVuSans.ttf", "arial.ttf", "C:/Windows/Fonts/arial.ttf"):
        try:
            font = ImageFont.truetype(candidate, 42)
            break
        except OSError:
            continue
    image = Image.new("RGB", (1400, 200), "white")
    ImageDraw.Draw(image).text((30, 60), text, fill="black", font=font)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@override_settings(OCR_ENGINE_BACKEND="paddle")
def test_real_ocr_reads_cyrillic_and_kazakh(tmp_path):
    from apps.ocr.services.ocr_engine import PaddleStructureEngine

    path = tmp_path / "line.png"
    path.write_bytes(_render("Қазақстан Республикасы Привет мир"))
    blocks = PaddleStructureEngine().recognize_page(path, "auto")
    joined = " ".join(b.text for b in blocks)
    assert "Привет" in joined
