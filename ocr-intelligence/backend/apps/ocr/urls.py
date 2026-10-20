from django.urls import path

from . import views

app_name = "ocr"

urlpatterns = [
    path("jobs/", views.JobListCreateView.as_view(), name="job-list"),
    path("jobs/<uuid:pk>/", views.JobDetailView.as_view(), name="job-detail"),
    path(
        "jobs/<uuid:pk>/documents/<uuid:document_id>/download/",
        views.DocumentDownloadView.as_view(),
        name="document-download",
    ),
    path("jobs/<uuid:pk>/download-zip/", views.JobZipView.as_view(), name="job-zip"),
]
