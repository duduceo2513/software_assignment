# OCR Intelligence

Web platform that turns scanned documents (PDF, PNG, JPG, TIFF) in Kazakh, Russian and English into **editable Word (.docx)** files. Recognition runs locally with **PaddleOCR 3.x / PP-StructureV3** on CPU; no paid or external APIs.

> **Security notice:** the MVP has **no authentication**. Anyone who can reach the API can upload, read and delete documents. Do not publish it to the internet without adding access control.

## Architecture

```
React (Vite, Mantine) --/api--> Django REST --enqueue--> Redis --> Celery worker (PaddleOCR) --> DOCX in media/
                                    |                                      |
                                PostgreSQL <------- status / text ---------+
```

| Layer | Details |
|---|---|
| Frontend | React 19, Vite, TypeScript (strict), Mantine 8 + custom theme, Lucide, Axios, React Router, TanStack Query (polls a job every 2 s until it finishes) |
| Backend | Django 5.2, DRF, django-cors-headers; apps `common` (envelope, errors, health) and `ocr` (models, API, tasks, services) |
| OCR | `services/ocr_engine.py` (PP-StructureV3, cached per recognition model) -> `document_processor.py` (PDF/TIFF -> page images, PyMuPDF/Pillow) -> `word_exporter.py` (python-docx; real paragraphs, headings, tables; all pages in one DOCX) |
| Queue | Celery + Redis; worker concurrency 1 by default (CPU/memory friendly) |
| DB / files | PostgreSQL for metadata; originals and results in `MEDIA_ROOT` via `FileField` (never in the DB) |

Language options: **Auto / Kazakh / Russian / English**. Auto, Kazakh and Russian all use `cyrillic_PP-OCRv5_mobile_rec` (Cyrillic + Latin); English uses `en_PP-OCRv5_mobile_rec`. The app does not detect languages automatically.

DOCX is built with python-docx from PP-StructureV3 layout blocks (instead of `save_to_word()`), because that is the only way to merge many pages into one document and to control table conversion. HTML tables from the model become real Word tables (row/column spans supported).

### API

All JSON responses use `{"success": bool, "data": ..., "error": {"code", "message", "details"} | null}`.

```
GET    /api/health/
POST   /api/ocr/jobs/                                  multipart: files[] (1-2), language=auto|kk|ru|en
GET    /api/ocr/jobs/
GET    /api/ocr/jobs/{uuid}/
DELETE /api/ocr/jobs/{uuid}/
GET    /api/ocr/jobs/{uuid}/documents/{document_uuid}/download/   -> .docx
GET    /api/ocr/jobs/{uuid}/download-zip/                        -> .zip
```

Validation: extension + magic bytes + structural parse (PyMuPDF/Pillow), size (`OCR_MAX_FILE_SIZE_MB`, 20), files per job (`OCR_MAX_FILES_PER_JOB`, 2), pages (`OCR_MAX_PAGES_PER_DOCUMENT`, 30), sanitised file names, storage names are UUIDs. Logs never contain document text.

## Requirements

- Docker Desktop (Windows 11: WSL2 backend), ~8 GB RAM free, ~6 GB disk (image + model cache).
- For running without Docker: Python 3.12 (PaddlePaddle has no wheels for 3.13+/3.14 on all platforms), Node 20+, PostgreSQL and Redis (optional - see below).

## Run everything with Docker Compose (Windows 11 / PowerShell)

```powershell
git clone <your-repo-url>; cd ocr-intelligence      # or open the existing folder
Copy-Item .env.example .env
# edit .env: set DJANGO_SECRET_KEY and POSTGRES_PASSWORD
docker compose up --build
```

- App: <http://localhost:5173> (Vite proxies `/api` to Django)
- API: <http://localhost:8000/api/health/>
- Admin: create a user, then open <http://localhost:8000/admin/>

```powershell
docker compose exec backend python manage.py createsuperuser
```

The first OCR run downloads model weights (a few hundred MB) into the `ocr_models` volume; later runs, and container restarts, reuse them. Useful commands:

```powershell
docker compose logs -f worker      # watch OCR progress
docker compose down                # stop (keeps database, uploads and model cache)
docker compose down -v             # stop and delete all data
```

## Run without Docker (development)

Backend (SQLite is used automatically while `POSTGRES_HOST` is unset):

```powershell
cd backend
py -3.12 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements-ocr.txt          # full OCR runtime (use requirements.txt for API/tests only)
$env:DJANGO_DEBUG = "1"
python manage.py migrate
python manage.py runserver 8000
```

Worker (needs Redis, e.g. `docker run -p 6379:6379 redis:7-alpine`):

```powershell
$env:DJANGO_DEBUG = "1"
celery -A config worker -l info --pool=solo --concurrency=1     # --pool=solo is needed on Windows
```

Frontend:

```powershell
cd frontend
npm ci
npm run dev        # http://localhost:5173
npm run build      # type-check + production build
```

Set `VITE_API_BASE_URL` (or `VITE_PROXY_TARGET`) if the backend is not on `localhost:8000`; see `frontend/.env.example`.

## Verify OCR

1. Open <http://localhost:5173>, drop a scanned PDF (1-2 files), choose a language, press **Process Documents**.
2. The job page shows queue state and real page counts; when finished, **Download DOCX** (and **Download all as ZIP** for two files).
3. Real-model test inside the image:
   ```powershell
   docker compose run --rm --no-deps backend python -m pytest -m integration -o addopts=""
   ```

## Tests

```powershell
cd backend
pip install -r requirements.txt
python -m pytest            # fast unit/API tests; OCR engine is stubbed, no weights needed
```

Covered: health, job creation with 1 and 2 documents, unsupported/spoofed/corrupt files, size/page/file-count limits, status transitions (completed / failed / partially completed), DOCX structure (multi-page, real tables, Kazakh letters, no images), downloads and ZIP, queue failure, deletion. The `integration` marker runs real PaddleOCR and is excluded by default.

## Jenkins (Assignment 5)

1. Jenkins on a Linux agent with git, Python 3.10+ (venv), Docker; plugins: Pipeline, Git, GitHub, JUnit. The stock `jenkins/jenkins` image has no Python or Docker (build fails with `python3: not found`), so use the ready-made one from this repo on any machine:
   ```powershell
   docker compose -f docker-compose.jenkins.yml up -d --build
   docker compose -f docker-compose.jenkins.yml exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
   ```
   Open <http://localhost:8080>, install the suggested plugins, then create the job below.
2. New item -> **Pipeline** -> *Pipeline script from SCM* -> Git -> your GitHub repo. Script Path: `Jenkinsfile` (or `ocr-intelligence/Jenkinsfile` if the project sits in a sub-folder).
3. Trigger: GitHub repo -> Settings -> Webhooks -> Payload URL `https://<jenkins>/github-webhook/`, content type `application/json`, event *push*; in the job enable *GitHub hook trigger for GITScm polling*. If Jenkins is not reachable from GitHub, the `pollSCM` fallback in the Jenkinsfile checks every ~5 minutes.
4. Stages: Checkout -> install deps -> Django checks (+ migrations up to date) -> unit tests (JUnit report) -> Docker build (backend + frontend prod image, only after tests pass) -> SUCCESS/FAILURE.

Manual Docker builds:

```powershell
docker build -t ocr-intelligence-backend backend
docker build --target prod -t ocr-intelligence-frontend frontend
```

## Configuration

All settings live in `.env` (see `.env.example`): Django, PostgreSQL, Celery/Redis, upload limits, OCR model names, CPU threads. Secrets are never stored in the repo.

## Known limitations

- No authentication, no multi-user separation, no rate limiting.
- Layout fidelity is approximate: reading order, headings, paragraphs and tables are rebuilt; fonts, columns, images, stamps and exact positions are not. Figures are omitted from the DOCX (text inside them is kept when recognised).
- Accuracy depends on scan quality. In the end-to-end check, ordinary Kazakh/Russian/English sentences were recognised correctly, but the **Kazakh-specific letters (Ә Ғ Қ Ң Ө Ұ Ү Һ І) are not reliable** with `cyrillic_PP-OCRv5_mobile_rec`: in an isolated alphabet line several were misread, and in small table cells `Қ`/`қ`/`ұ` came out as `К`/`к`/`у`-like letters. Always proofread Kazakh output; a Kazakh-specific recognition model would be the next step.
- CPU only: about 40 s per page on a laptop-class CPU for the first pages (model warm-up included). Large documents take minutes.
- Page limit and one concurrent OCR job are deliberate stability trade-offs.
