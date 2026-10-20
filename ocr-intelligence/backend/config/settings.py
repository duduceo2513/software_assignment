"""Django settings for OCR Intelligence. All configuration comes from the environment."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    """Load KEY=VALUE pairs from backend/.env or the repo-root .env without overriding real env vars."""
    for candidate in (BASE_DIR / ".env", BASE_DIR.parent / ".env"):
        if not candidate.is_file():
            continue
        for line in candidate.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
        break


_load_dotenv()


def env_str(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def env_int(name: str, default: int) -> int:
    return int(os.environ.get(name, default))


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


DEBUG = env_bool("DJANGO_DEBUG", False)
SECRET_KEY = env_str("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "insecure-dev-only-key-change-me"
    else:
        raise RuntimeError("DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is false")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "apps.common",
    "apps.ocr",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Database: PostgreSQL when POSTGRES_HOST is set, SQLite otherwise (local smoke runs / CI) ---
if env_str("POSTGRES_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env_str("POSTGRES_DB", "ocr_intelligence"),
            "USER": env_str("POSTGRES_USER", "ocr"),
            "PASSWORD": env_str("POSTGRES_PASSWORD"),
            "HOST": env_str("POSTGRES_HOST"),
            "PORT": env_str("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = env_str("DJANGO_TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = Path(env_str("MEDIA_ROOT", str(BASE_DIR / "media")))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- CORS ---
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
CORS_EXPOSE_HEADERS = ["Content-Disposition"]

# --- DRF ---
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    # The MVP has no authentication: do NOT expose the OCR endpoints to the internet as-is.
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "EXCEPTION_HANDLER": "apps.common.exceptions.api_exception_handler",
    "UNAUTHENTICATED_USER": None,
}

# --- Upload limits ---
OCR_MAX_FILE_SIZE_MB = env_int("OCR_MAX_FILE_SIZE_MB", 20)
OCR_MAX_FILES_PER_JOB = env_int("OCR_MAX_FILES_PER_JOB", 2)
OCR_MAX_PAGES_PER_DOCUMENT = env_int("OCR_MAX_PAGES_PER_DOCUMENT", 30)
OCR_MAX_IMAGE_PIXELS = env_int("OCR_MAX_IMAGE_PIXELS", 60_000_000)
OCR_PDF_RENDER_DPI = env_int("OCR_PDF_RENDER_DPI", 200)
DATA_UPLOAD_MAX_MEMORY_SIZE = (OCR_MAX_FILE_SIZE_MB * OCR_MAX_FILES_PER_JOB + 2) * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# --- OCR engine ---
OCR_ENGINE_BACKEND = env_str("OCR_ENGINE_BACKEND", "paddle")  # "paddle" | "unavailable"
OCR_MULTILINGUAL_REC_MODEL = env_str("OCR_MULTILINGUAL_REC_MODEL", "cyrillic_PP-OCRv5_mobile_rec")
OCR_ENGLISH_REC_MODEL = env_str("OCR_ENGLISH_REC_MODEL", "en_PP-OCRv5_mobile_rec")
OCR_DETECTION_MODEL = env_str("OCR_DETECTION_MODEL", "PP-OCRv5_mobile_det")
OCR_CPU_THREADS = env_int("OCR_CPU_THREADS", 4)

# --- Celery ---
CELERY_BROKER_URL = env_str("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env_str("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", False)
CELERY_TASK_EAGER_PROPAGATES = False
CELERY_WORKER_CONCURRENCY = env_int("CELERY_WORKER_CONCURRENCY", 1)
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_MAX_TASKS_PER_CHILD = env_int("CELERY_WORKER_MAX_TASKS_PER_CHILD", 20)
CELERY_TASK_TIME_LIMIT = env_int("CELERY_TASK_TIME_LIMIT", 3600)
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# --- Logging (never log document content) ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"simple": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "root": {"handlers": ["console"], "level": env_str("LOG_LEVEL", "INFO")},
}
