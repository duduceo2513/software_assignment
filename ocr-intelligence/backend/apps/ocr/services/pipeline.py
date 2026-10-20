"""Orchestration of OCR jobs: page rendering -> recognition -> DOCX export -> status updates.

Kept free of HTTP concerns; called from Celery tasks (and directly from tests).
"""
import logging
import tempfile
import time
from pathlib import Path

from django.core.files import File
from django.db import transaction
from django.utils import timezone

from ..models import DocumentStatus, JobStatus, OCRDocument, OCRJob, OCRPage
from . import ocr_engine
from .document_processor import iter_page_images
from .ocr_engine import OCREngineUnavailable, PageResult
from .word_exporter import block_plain_text, export_docx

logger = logging.getLogger(__name__)


def process_job(job_id: str) -> None:
    job = OCRJob.objects.filter(pk=job_id).first()
    if job is None or job.is_finished:
        return
    job.status = JobStatus.PROCESSING
    job.started_at = job.started_at or timezone.now()
    job.save(update_fields=["status", "started_at"])

    for document in job.documents.filter(status__in=[DocumentStatus.PENDING, DocumentStatus.PROCESSING]):
        process_document(document)

    finalize_job(job)


def finalize_job(job: OCRJob) -> None:
    statuses = list(job.documents.values_list("status", flat=True))
    completed = statuses.count(DocumentStatus.COMPLETED)
    failed = statuses.count(DocumentStatus.FAILED)
    if statuses and completed == len(statuses):
        job.status = JobStatus.COMPLETED
    elif completed and failed:
        job.status = JobStatus.PARTIALLY_COMPLETED
    else:
        job.status = JobStatus.FAILED
        errors = job.documents.exclude(error_message="").values_list("error_message", flat=True)
        job.error_message = next(iter(errors), "Processing failed.")
    job.finished_at = timezone.now()
    job.save(update_fields=["status", "finished_at", "error_message"])


def process_document(document: OCRDocument) -> None:
    started = time.monotonic()
    document.status = DocumentStatus.PROCESSING
    document.pages_processed = 0
    document.error_message = ""
    document.save(update_fields=["status", "pages_processed", "error_message"])
    try:
        pages = _recognize(document)
        with tempfile.TemporaryDirectory(prefix="ocr-docx-") as tmp:
            output = Path(tmp) / "result.docx"
            text = export_docx(pages, output, title=document.original_filename)
            with output.open("rb") as handle:
                if document.result_docx:
                    document.result_docx.delete(save=False)
                document.result_docx.save(document.download_filename, File(handle), save=False)
        _store_pages(document, pages)
        document.recognized_text = text
        document.status = DocumentStatus.COMPLETED
    except OCREngineUnavailable as exc:
        logger.error("OCR engine unavailable for document %s: %s", document.pk, exc)
        document.status = DocumentStatus.FAILED
        document.error_message = str(exc)
    except Exception as exc:  # noqa: BLE001 - one bad document must not stop the job
        logger.exception("Document %s failed (%s)", document.pk, type(exc).__name__)
        document.status = DocumentStatus.FAILED
        document.error_message = f"Could not process this document ({type(exc).__name__})."
    document.processing_seconds = round(time.monotonic() - started, 2)
    document.finished_at = timezone.now()
    document.save()


def _recognize(document: OCRDocument) -> list[PageResult]:
    engine = ocr_engine.get_engine()
    pages: list[PageResult] = []
    with tempfile.TemporaryDirectory(prefix="ocr-pages-") as tmp:
        for number, image_path in iter_page_images(
            Path(document.source_file.path), document.mime_type, Path(tmp)
        ):
            blocks = engine.recognize_page(image_path, document.language)
            pages.append(PageResult(number=number, blocks=blocks))
            image_path.unlink(missing_ok=True)
            document.pages_processed = number
            document.save(update_fields=["pages_processed"])
    return pages


@transaction.atomic
def _store_pages(document: OCRDocument, pages: list[PageResult]) -> None:
    document.pages.all().delete()
    OCRPage.objects.bulk_create(
        OCRPage(
            document=document,
            number=page.number,
            text="\n".join(filter(None, (block_plain_text(b) for b in page.blocks))),
            blocks_count=len(page.blocks),
            tables_count=sum(1 for b in page.blocks if b.table_html),
        )
        for page in pages
    )
    document.page_count = len(pages) or document.page_count
