"""Settings for unit tests / CI: SQLite, eager Celery, temp media, mocked OCR."""
import os
import tempfile

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-secret-key")

from .settings import *  # noqa: F401,F403

DEBUG = False
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
MEDIA_ROOT = tempfile.mkdtemp(prefix="ocr-test-media-")
CELERY_TASK_ALWAYS_EAGER = True
OCR_ENGINE_BACKEND = "unavailable"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
