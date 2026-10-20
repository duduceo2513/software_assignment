"""PaddleOCR 3.x (PP-StructureV3) engine.

The pipeline objects are heavy (they load detection, layout, table and recognition weights), so they are
created once per recognition model and cached for the lifetime of the worker process.
"""
import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from django.conf import settings

logger = logging.getLogger(__name__)


class OCREngineUnavailable(RuntimeError):
    """The OCR runtime (PaddlePaddle / PaddleOCR) is not installed or failed to initialise."""


@dataclass
class Block:
    """A layout block in reading order. `table_html` is set for tables."""

    label: str
    text: str = ""
    bbox: tuple[float, ...] = ()
    table_html: str | None = None


@dataclass
class PageResult:
    number: int
    blocks: list[Block] = field(default_factory=list)


class OCREngine(Protocol):
    def recognize_page(self, image_path: Path, language: str) -> list[Block]: ...


def recognition_model_for(language: str) -> str:
    """English-only documents use the dedicated English model; everything else uses the
    multilingual Cyrillic+Latin model (it covers Kazakh, Russian and English text)."""
    if language == "en":
        return settings.OCR_ENGLISH_REC_MODEL
    return settings.OCR_MULTILINGUAL_REC_MODEL


class PaddleStructureEngine:
    def __init__(self) -> None:
        self._pipelines: dict[str, object] = {}
        self._lock = threading.Lock()

    def _get_pipeline(self, rec_model: str):
        with self._lock:
            pipeline = self._pipelines.get(rec_model)
            if pipeline is not None:
                return pipeline
            try:
                from paddleocr import PPStructureV3
            except ImportError as exc:
                raise OCREngineUnavailable(
                    "PaddleOCR is not installed in this environment (pip install -r requirements-ocr.txt)."
                ) from exc
            logger.info("Initialising PP-StructureV3 with recognition model %s", rec_model)
            try:
                pipeline = PPStructureV3(
                    text_recognition_model_name=rec_model,
                    text_detection_model_name=settings.OCR_DETECTION_MODEL,
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                    use_seal_recognition=False,
                    use_formula_recognition=False,
                    use_chart_recognition=False,
                    device="cpu",
                    cpu_threads=settings.OCR_CPU_THREADS,
                )
            except Exception as exc:  # noqa: BLE001
                raise OCREngineUnavailable(f"Failed to initialise PP-StructureV3: {exc}") from exc
            self._pipelines[rec_model] = pipeline
            return pipeline

    def recognize_page(self, image_path: Path, language: str) -> list[Block]:
        pipeline = self._get_pipeline(recognition_model_for(language))
        results = pipeline.predict(input=str(image_path))
        blocks: list[Block] = []
        for result in results:
            blocks.extend(parse_structure_result(result))
        return blocks


def parse_structure_result(result) -> list[Block]:
    """Convert one PP-StructureV3 result object (or its JSON dict) to Blocks, tolerating minor
    schema differences between PaddleOCR 3.x releases."""
    data = getattr(result, "json", result)
    if callable(data):
        data = data()
    if isinstance(data, dict) and isinstance(data.get("res"), dict):
        data = data["res"]
    if not isinstance(data, dict):
        return []

    tables_html = [t.get("pred_html") for t in data.get("table_res_list", []) or [] if isinstance(t, dict)]
    table_index = 0
    blocks: list[Block] = []
    for item in data.get("parsing_res_list", []) or []:
        label = str(item.get("block_label", "text"))
        content = str(item.get("block_content") or "").strip()
        bbox = tuple(item.get("block_bbox") or ())
        if label == "table":
            html = content if "<table" in content.lower() else None
            if html is None and table_index < len(tables_html):
                html = tables_html[table_index]
            table_index += 1
            if html:
                blocks.append(Block(label, "", bbox, html))
                continue
        if content:
            blocks.append(Block(label, content, bbox))

    if not blocks:
        # Layout parsing produced nothing: fall back to raw OCR lines so no recognised text is lost.
        ocr = data.get("overall_ocr_res") or {}
        for line in ocr.get("rec_texts", []) or []:
            if str(line).strip():
                blocks.append(Block("text", str(line).strip()))
    return blocks


class UnavailableEngine:
    def recognize_page(self, image_path: Path, language: str) -> list[Block]:
        raise OCREngineUnavailable("OCR engine is disabled (OCR_ENGINE_BACKEND=unavailable).")


_engine: OCREngine | None = None
_engine_lock = threading.Lock()


def get_engine() -> OCREngine:
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = UnavailableEngine() if settings.OCR_ENGINE_BACKEND == "unavailable" else PaddleStructureEngine()
        return _engine
