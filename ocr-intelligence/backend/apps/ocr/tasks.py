from celery import shared_task

from .services.pipeline import process_job


@shared_task(name="ocr.process_job")
def process_ocr_job(job_id: str) -> None:
    process_job(job_id)
