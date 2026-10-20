import io
import logging
import shutil
import zipfile
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView

from apps.common.exceptions import ApiError
from apps.common.responses import success_response

from .models import DocumentStatus, JobStatus, OCRDocument, OCRJob
from .serializers import JobCreateSerializer, OCRJobSerializer
from .tasks import process_ocr_job

logger = logging.getLogger(__name__)

LIST_LIMIT = 100


def _job_queryset():
    return OCRJob.objects.prefetch_related("documents")


def _dispatch(job_id: str) -> None:
    try:
        process_ocr_job.delay(job_id)
    except Exception:  # noqa: BLE001 - broker down; the job must not stay "pending" forever
        logger.exception("Could not enqueue OCR job %s", job_id)
        OCRJob.objects.filter(pk=job_id).update(
            status=JobStatus.FAILED, error_message="The processing queue is unavailable. Try again later."
        )
        OCRDocument.objects.filter(job_id=job_id).update(
            status=DocumentStatus.FAILED, error_message="The processing queue is unavailable."
        )


class JobListCreateView(APIView):
    def get(self, request):
        try:
            limit = max(1, min(int(request.query_params.get("limit", LIST_LIMIT)), 500))
        except ValueError:
            limit = LIST_LIMIT
        jobs = _job_queryset()[:limit]
        return success_response(OCRJobSerializer(jobs, many=True).data)

    def post(self, request):
        files = request.FILES.getlist("files[]") or request.FILES.getlist("files")
        serializer = JobCreateSerializer(data=request.data, files=files)
        serializer.is_valid(raise_exception=True)
        language = serializer.validated_data["language"]
        validated = serializer.validated_files

        with transaction.atomic():
            title = " + ".join(item.filename for _, item in validated)[:255]
            job = OCRJob.objects.create(title=title, language=language, documents_count=len(validated))
            for uploaded, item in validated:
                document = OCRDocument(
                    job=job,
                    original_filename=item.filename,
                    mime_type=item.mime_type,
                    file_size=item.size,
                    page_count=item.page_count,
                    language=language,
                )
                document.source_file.save(item.filename, uploaded, save=False)
                document.save()
            transaction.on_commit(lambda: _dispatch(str(job.id)))

        job = _job_queryset().get(pk=job.pk)
        return success_response(OCRJobSerializer(job).data, status.HTTP_201_CREATED)


class JobDetailView(APIView):
    def get(self, request, pk):
        job = get_object_or_404(_job_queryset(), pk=pk)
        return success_response(OCRJobSerializer(job).data)

    def delete(self, request, pk):
        job = get_object_or_404(_job_queryset(), pk=pk)
        if job.status == JobStatus.PROCESSING:
            raise ApiError("The job is being processed; wait until it finishes.", "job_busy", status.HTTP_409_CONFLICT)
        for document in job.documents.all():
            document.source_file.delete(save=False)
            if document.result_docx:
                document.result_docx.delete(save=False)
        job.delete()
        for folder in ("uploads", "results"):
            shutil.rmtree(Path(settings.MEDIA_ROOT) / folder / str(pk), ignore_errors=True)
        return success_response({"deleted": True})


class DocumentDownloadView(APIView):
    def get(self, request, pk, document_id):
        document = get_object_or_404(OCRDocument, pk=document_id, job_id=pk)
        if document.status != DocumentStatus.COMPLETED or not document.result_docx:
            raise ApiError("The Word file is not ready yet.", "not_ready", status.HTTP_409_CONFLICT)
        try:
            handle = document.result_docx.open("rb")
        except FileNotFoundError as exc:
            raise ApiError(
                "The result file is missing on the server.", "file_missing", status.HTTP_404_NOT_FOUND
            ) from exc
        return FileResponse(handle, as_attachment=True, filename=document.download_filename)


class JobZipView(APIView):
    def get(self, request, pk):
        job = get_object_or_404(_job_queryset(), pk=pk)
        documents = [d for d in job.documents.all() if d.status == DocumentStatus.COMPLETED and d.result_docx]
        if not documents:
            raise ApiError("There are no finished documents to download.", "not_ready", status.HTTP_409_CONFLICT)

        buffer = io.BytesIO()
        used: set[str] = set()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for document in documents:
                name, counter = document.download_filename, 1
                while name in used:
                    counter += 1
                    name = f"{Path(document.download_filename).stem} ({counter}).docx"
                used.add(name)
                with document.result_docx.open("rb") as handle:
                    archive.writestr(name, handle.read())
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f"ocr-results-{str(job.id)[:8]}.zip")
