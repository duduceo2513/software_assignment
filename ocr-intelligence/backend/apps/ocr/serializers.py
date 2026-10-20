from django.conf import settings
from django.urls import reverse
from rest_framework import serializers

from .models import DocumentStatus, Language, OCRDocument, OCRJob
from .services.file_validator import FileValidationError, ValidatedFile, validate_upload

TEXT_PREVIEW_CHARS = 5000


class OCRDocumentSerializer(serializers.ModelSerializer):
    text_preview = serializers.SerializerMethodField()
    has_result = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = OCRDocument
        fields = [
            "id", "original_filename", "mime_type", "file_size", "page_count", "pages_processed",
            "language", "status", "processing_seconds", "created_at", "finished_at", "error_message",
            "text_preview", "has_result", "download_url",
        ]  # fmt: skip
        read_only_fields = fields

    def get_text_preview(self, obj: OCRDocument) -> str:
        return obj.recognized_text[:TEXT_PREVIEW_CHARS]

    def get_has_result(self, obj: OCRDocument) -> bool:
        return obj.status == DocumentStatus.COMPLETED and bool(obj.result_docx)

    def get_download_url(self, obj: OCRDocument) -> str | None:
        if not self.get_has_result(obj):
            return None
        return reverse("ocr:document-download", kwargs={"pk": obj.job_id, "document_id": obj.id})


class OCRJobSerializer(serializers.ModelSerializer):
    documents = OCRDocumentSerializer(many=True, read_only=True)
    is_finished = serializers.BooleanField(read_only=True)
    zip_url = serializers.SerializerMethodField()

    class Meta:
        model = OCRJob
        fields = [
            "id", "title", "status", "language", "documents_count", "created_at", "started_at",
            "finished_at", "error_message", "is_finished", "documents", "zip_url",
        ]  # fmt: skip
        read_only_fields = fields

    def get_zip_url(self, obj: OCRJob) -> str | None:
        completed = [d for d in obj.documents.all() if d.status == DocumentStatus.COMPLETED and d.result_docx]
        if not completed or obj.documents_count < 2:
            return None
        return reverse("ocr:job-zip", kwargs={"pk": obj.id})


class JobCreateSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=Language.choices, default=Language.AUTO)

    def __init__(self, *args, files=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._files = list(files or [])
        self.validated_files: list[tuple[object, ValidatedFile]] = []

    def validate(self, attrs):
        limit = settings.OCR_MAX_FILES_PER_JOB
        if not self._files:
            raise serializers.ValidationError("Attach at least one document (field 'files[]').")
        if len(self._files) > limit:
            raise serializers.ValidationError(f"At most {limit} documents per job.")
        for uploaded in self._files:
            try:
                self.validated_files.append((uploaded, validate_upload(uploaded)))
            except FileValidationError as exc:
                raise serializers.ValidationError(str(exc)) from exc
        return attrs
