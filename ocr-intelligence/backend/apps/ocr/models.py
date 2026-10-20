import uuid
from pathlib import PurePath

from django.db import models


class Language(models.TextChoices):
    AUTO = "auto", "Auto (multilingual Cyrillic + Latin)"
    KAZAKH = "kk", "Kazakh"
    RUSSIAN = "ru", "Russian"
    ENGLISH = "en", "English"


class JobStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    PARTIALLY_COMPLETED = "partially_completed", "Partially completed"


class DocumentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


def source_upload_path(instance: "OCRDocument", filename: str) -> str:
    suffix = PurePath(filename).suffix.lower()
    return f"uploads/{instance.job_id}/{instance.id}{suffix}"


def result_upload_path(instance: "OCRDocument", filename: str) -> str:
    return f"results/{instance.job_id}/{instance.id}.docx"


class OCRJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=24, choices=JobStatus.choices, default=JobStatus.PENDING, db_index=True)
    language = models.CharField(max_length=8, choices=Language.choices, default=Language.AUTO)
    documents_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} [{self.status}]"

    @property
    def is_finished(self) -> bool:
        return self.status in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.PARTIALLY_COMPLETED}


class OCRDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(OCRJob, related_name="documents", on_delete=models.CASCADE)
    original_filename = models.CharField(max_length=255)
    source_file = models.FileField(upload_to=source_upload_path, max_length=300)
    result_docx = models.FileField(upload_to=result_upload_path, max_length=300, blank=True, null=True)
    mime_type = models.CharField(max_length=100)
    file_size = models.PositiveBigIntegerField(default=0)
    page_count = models.PositiveIntegerField(default=0)
    pages_processed = models.PositiveIntegerField(default=0)
    language = models.CharField(max_length=8, choices=Language.choices, default=Language.AUTO)
    status = models.CharField(
        max_length=16, choices=DocumentStatus.choices, default=DocumentStatus.PENDING, db_index=True
    )
    recognized_text = models.TextField(blank=True, default="")
    processing_seconds = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return self.original_filename

    @property
    def download_filename(self) -> str:
        return f"{PurePath(self.original_filename).stem or 'document'}.docx"


class OCRPage(models.Model):
    document = models.ForeignKey(OCRDocument, related_name="pages", on_delete=models.CASCADE)
    number = models.PositiveIntegerField()
    text = models.TextField(blank=True, default="")
    blocks_count = models.PositiveIntegerField(default=0)
    tables_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["document", "number"]
        constraints = [models.UniqueConstraint(fields=["document", "number"], name="uniq_page_per_document")]

    def __str__(self) -> str:
        return f"{self.document_id} p.{self.number}"
