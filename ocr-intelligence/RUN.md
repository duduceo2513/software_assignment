# Запуск OCR Intelligence

Команды ниже для **Windows CMD** (для macOS/Linux см. раздел 8). Выполняйте их из папки проекта:

```bat
cd /d C:\Users\verst\Documents\DEV\software_assiks\ocr-intelligence
```

## 1. Что нужно

| Что | Зачем |
|---|---|
| Docker Desktop (запущен, Windows или macOS) | запуск всего проекта и Jenkins |
| Git | клонирование и push |
| ~8 ГБ свободной RAM, ~6 ГБ диска | образы и модели OCR |
| Node.js 20+ и Python 3.12 | только для запуска **без** Docker |

## 2. Запуск всего проекта через Docker (рекомендуется)

Это единственный вариант, где работает **настоящий OCR**.

### 2.1 Файл настроек

Файл `.env` лежит в корне проекта. Если его нет:

```bat
copy .env.example .env
```

Минимально важные значения в `.env` (в `.env.example` они уже заданы):

```env
DJANGO_SECRET_KEY=ocr_engine_django_s3cr3t_k3y_0pt10n
POSTGRES_PASSWORD=ocr_engine_pg_p4ssw0rd
```

### 2.2 Старт

```bat
docker compose up --build
```

Фоновый режим (без логов в терминале):

```bat
docker compose up -d --build
docker compose logs -f          # смотреть логи, выход: Ctrl+C
```

### 2.3 Что запускается

| Контейнер | Что это | Адрес |
|---|---|---|
| `frontend` | React (Vite) | <http://localhost:5173> |
| `backend` | Django API | <http://localhost:8000/api/health/> |
| `worker` | Celery, выполняет OCR | - |
| `postgres` | база данных | внутри сети Docker |
| `redis` | очередь задач | внутри сети Docker |

Открывайте интерфейс: **<http://localhost:5173>**.

> При первой загрузке документа PaddleOCR скачивает модели (несколько сотен МБ).
> Они сохраняются в Docker-томе `ocr_models` и больше не скачиваются.

### 2.4 Проверка работы

1. Откройте <http://localhost:5173>.
2. Перетащите PDF/PNG/JPG/TIFF (1-2 файла), выберите язык.
3. Нажмите **Process Documents**.
4. На странице результата нажмите **Download DOCX** (для двух файлов ещё **Download all as ZIP**).

Проверка API из терминала:

```bat
curl http://localhost:8000/api/health/
```

### 2.5 Админка Django

```bat
docker compose exec backend python manage.py createsuperuser
```

Затем: <http://localhost:8000/admin/>

### 2.6 Остановка

```bat
docker compose stop        # остановить, ничего не удаляя
docker compose down        # удалить контейнеры (данные и модели сохраняются)
docker compose down -v     # удалить ВСЁ, включая базу, файлы и кэш моделей
```

### 2.7 После изменений в коде

Контейнеры собираются из копии кода, поэтому после правок нужна пересборка:

```bat
docker compose up -d --build frontend     # только фронтенд
docker compose up -d --build              # всё
```

## 3. Тесты

### 3.1 Быстрые тесты (без OCR-моделей)

```bat
cd backend
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python -m pytest
```

Ожидаемый результат: `25 passed, 1 deselected`.

### 3.2 Тест с реальной моделью (медленный, нужен Docker)

```bat
docker compose run --rm --no-deps backend python -m pytest -m integration -o addopts=""
```

### 3.3 Сборка и проверка типов фронтенда

```bat
cd frontend
npm ci
npm run build
```

## 4. Запуск без Docker (только для разработки)

Работают интерфейс, API, загрузка и история. **OCR не работает**, потому что для него нужны Celery + Redis и Python 3.12 с PaddleOCR.

Backend (SQLite используется автоматически, `.env` читается сам):

```bat
cd backend
venv\Scripts\activate.bat
python manage.py migrate
python manage.py runserver 8000
```

Frontend (в другом терминале):

```bat
cd frontend
npm ci
npm run dev
```

Откройте <http://localhost:5173>. Не запускайте этот режим одновременно с Docker: порты 8000 и 5173 будут заняты.

## 5. Jenkins (CI)

Jenkins описан в репозитории: `jenkins/Dockerfile` (Jenkins + Python + Docker CLI) и `docker-compose.jenkins.yml` (подключает Docker вашего компьютера).

### 5.1 Запуск Jenkins

Если на порту 8080 уже работает другой Jenkins, остановите его:

```bat
docker stop ocr-jenkins
```

Запуск:

```bat
docker compose -f docker-compose.jenkins.yml up -d --build
```

Первоначальный пароль администратора:

```bat
docker compose -f docker-compose.jenkins.yml exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Проверка, что внутри есть Python и Docker:

```bat
docker compose -f docker-compose.jenkins.yml exec jenkins sh -c "python3 --version; docker info > /dev/null 2>&1 && echo DOCKER_OK"
```

### 5.2 Первичная настройка

1. Откройте <http://localhost:8080>.
2. Введите пароль из команды выше.
3. Нажмите **Install suggested plugins**.
4. Создайте администратора.

### 5.3 Создание job

1. **New Item** -> имя `OCR-Intelligence-CI` -> тип **Pipeline** -> OK.
2. Раздел **Pipeline**:

| Поле | Значение |
|---|---|
| Definition | Pipeline script from SCM |
| SCM | Git |
| Repository URL | URL вашего GitHub-репозитория, например `https://github.com/duduceo2513/software_assiks.git` |
| Branch Specifier | `*/main` |
| **Script Path** | `ocr-intelligence/Jenkinsfile` |

3. Нажмите **Save**, затем **Build Now**.

> Проверьте URL: локальный репозиторий смотрит на `software_assiks.git`, а в логах Jenkins был `software_assignment.git`. Нужен тот, куда вы делаете push.

### 5.4 Что делает пайплайн

| Этап | Действие |
|---|---|
| Checkout | клонирует репозиторий |
| Install test dependencies | ставит Python-зависимости (при необходимости сам скачивает Python 3.12) |
| Django checks | `manage.py check` и проверка миграций |
| Unit tests | 25 тестов + отчёт JUnit |
| Docker build | собирает образы backend и frontend (только после успешных тестов) |

Итоги: **SUCCESS** - всё прошло. **UNSTABLE** - тесты прошли, но Docker недоступен. **FAILURE** - ошибка.

### 5.5 Автозапуск при push (webhook, необязательно)

В job включите **Build Triggers -> GitHub hook trigger for GITScm polling**, а в GitHub: **Settings -> Webhooks -> Add webhook**:

| Поле | Значение |
|---|---|
| Payload URL | `https://<адрес-jenkins>/github-webhook/` |
| Content type | `application/json` |
| Event | Just the push event |

Если Jenkins не виден из интернета (localhost), сработает запасной вариант из Jenkinsfile: проверка репозитория раз в ~5 минут (`pollSCM`).

### 5.6 Остановка Jenkins

```bat
docker compose -f docker-compose.jenkins.yml stop
```

## 6. Git: отправка изменений

```bat
cd /d C:\Users\verst\Documents\DEV\software_assiks
git add ocr-intelligence
git status
git commit -m "Update OCR Intelligence"
git push origin main
```

## 7. Частые проблемы

| Симптом | Решение |
|---|---|
| `DJANGO_SECRET_KEY must be set...` | запускайте из папки проекта; `.env` должен лежать в `ocr-intelligence/` |
| `password authentication failed for user "ocr"` | пароль в `.env` изменён после создания базы. Либо `docker compose down -v`, либо `docker compose exec postgres psql -U ocr -d ocr_intelligence -c "ALTER USER ocr PASSWORD 'новый_пароль';"` |
| Порт 8000, 5173 или 8080 занят | остановите другой процесс или контейнер: `docker ps`, затем `docker stop <имя>` |
| Изменения в коде не видны в браузере | `docker compose up -d --build frontend` и Ctrl+F5 |
| Jenkins: `python3: not found` | используйте Jenkins из `docker-compose.jenkins.yml` |
| Jenkins: итог UNSTABLE | Jenkins не видит Docker: запустите его через `docker-compose.jenkins.yml` |
| Первый OCR очень долгий | идёт скачивание моделей, подождите; повторные запуски быстрее |
| Казахские буквы распознаны неверно | известное ограничение модели, результат нужно вычитывать |

## 8. macOS / Linux (Terminal)

Docker-часть **не отличается**: те же `docker compose ...` и тот же `docker-compose.jenkins.yml`, те же адреса и порты. Меняются только команды оболочки.

```bash
cd ~/путь/к/software_assiks/ocr-intelligence
cp .env.example .env
docker compose up --build
```

| Windows CMD | macOS / Linux |
|---|---|
| `cd /d C:\Users\...\ocr-intelligence` | `cd ~/путь/к/ocr-intelligence` |
| `copy .env.example .env` | `cp .env.example .env` |
| `python -m venv venv` | `python3 -m venv venv` |
| `venv\Scripts\activate.bat` | `source venv/bin/activate` |
| `python ...` | `python3 ...` (внутри активного venv можно `python`) |

Тесты и запуск без Docker на macOS:

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m pytest
python manage.py migrate && python manage.py runserver 8000
```

```bash
cd frontend && npm ci && npm run dev
```

Jenkins на macOS:

```bash
docker compose -f docker-compose.jenkins.yml up -d --build
docker compose -f docker-compose.jenkins.yml exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Особенности macOS:

- Docker Desktop должен быть запущен; в его настройках выделите Docker минимум 6-8 ГБ памяти (Settings -> Resources).
- На Mac с чипом Apple (M1/M2/M3...) образы собираются под ARM. Я проверял проект только на Windows (x86-64). Если сборка backend упадёт на установке PaddlePaddle, добавьте в `docker-compose.yml` сервисам `backend` и `worker` строку `platform: linux/amd64` (работает, но OCR будет заметно медленнее из-за эмуляции).
- Сокет Docker `/var/run/docker.sock` для Jenkins там тот же, менять compose не нужно.
