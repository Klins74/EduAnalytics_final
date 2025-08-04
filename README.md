# EduAnalytics AI

Система аналитики успеваемости учащихся с использованием искусственного интеллекта.

## Технологии

### Фронтенд
- React 18
- Vite
- Tailwind CSS
- Google Generative AI (Gemini)
- Sentry для мониторинга ошибок

### Бэкенд
- FastAPI
- SQLAlchemy (Async)
- PostgreSQL
- Redis
- Alembic для миграций
- Sentry для мониторинга ошибок

## Установка и запуск

### Предварительные требования
- Docker и Docker Compose
- Node.js 18+
- Python 3.10+

### Настройка переменных окружения

1. Создайте файл `.env` в корне проекта на основе `.env.example`:
```bash
cp .env.example .env
```

2. Создайте файл `.env.local` в корне проекта для фронтенда на основе `.env.local.example`:
```bash
cp .env.local.example .env.local
```

3. При необходимости отредактируйте переменные окружения в созданных файлах.

### Запуск с использованием Docker

```bash
docker-compose up -d
```

Это запустит:
- Бэкенд на FastAPI (http://localhost:8000)
- PostgreSQL базу данных
- Redis для кэширования

### Запуск фронтенда для разработки

```bash
npm install
npm start
```

Фронтенд будет доступен по адресу http://localhost:5173

## Мониторинг ошибок с Sentry

Проект настроен для отслеживания ошибок с помощью Sentry как на фронтенде, так и на бэкенде.

### Настройка Sentry

1. Создайте аккаунт на [Sentry.io](https://sentry.io/)
2. Создайте проекты для React и FastAPI
3. Получите DSN ключи для каждого проекта
4. Добавьте ключи в соответствующие файлы переменных окружения:
   - Для фронтенда: `VITE_SENTRY_DSN` в `.env.local`
   - Для бэкенда: `SENTRY_DSN` в `.env`

### Настройка для CI/CD

Для работы с Sentry в CI/CD, добавьте следующие секреты в настройки GitHub Actions:

- `SENTRY_AUTH_TOKEN` - токен авторизации Sentry
- `SENTRY_ORG` - название вашей организации в Sentry
- `SENTRY_PROJECT` - название проекта в Sentry

## Лицензия

MIT

# EduAnalytics Monorepo (Stage 0)

## Структура
- `eduanalytics-backend` — FastAPI backend (будет вынесен в отдельный репозиторий)
- `eduanalytics-frontend` — Next.js frontend (будет вынесен в отдельный репозиторий)
- `docker-compose.yml` — локальная dev-среда для одновременного запуска всех сервисов

## Шаги разделения репозиториев
1. Создать два отдельных репозитория на GitHub:
   - `eduanalytics-backend`
   - `eduanalytics-frontend`
2. Перенести содержимое папки `server` в новый репозиторий `eduanalytics-backend`.
3. Перенести содержимое папки `src` и frontend-конфиги в новый репозиторий `eduanalytics-frontend`.
4. В каждом репозитории добавить:
   - README.md с описанием
   - .gitignore (Python для backend, Node для frontend)
   - LICENSE (MIT или другая)
5. В корне каждого репозитория создать `.github/workflows/ci.yml` для CI/CD.

## Пример .gitignore для backend (Python)
```
# Python
__pycache__/
*.py[cod]
*.egg-info/
.env
.env.*

# VSCode
.vscode/

# Docker
*.db
*.sqlite3

# Alembic
alembic/versions/
```

## Пример .gitignore для frontend (Node)
```
# Node
node_modules/
.next/
dist/
.env
.env.*

# VSCode
.vscode/
```

## Итог
- Два отдельных репозитория с чистой структурой, готовые к CI/CD и дальнейшей настройке инфраструктуры.

## Canvas LMS в Docker

### Шаги запуска:
1. Убедитесь, что в .env заданы переменные CANVAS_SECRET_KEY, CANVAS_LMS_DOMAIN, CANVAS_LMS_REDIS_URL, CANVAS_LMS_ELASTICSEARCH_URL, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB.
2. Запустите команду:
   ```sh
   docker-compose up canvas db cache elasticsearch
   ```
3. Canvas LMS будет доступен на http://localhost:8080
4. Для инициализации Canvas LMS используйте официальную документацию: https://github.com/instructure/canvas-lms

## Управление секретами и переменными окружения

### Шаги:
1. Все секреты (CANVAS_TOKEN, DB_URL, JWT_SECRET и др.) должны храниться только в `.env` (или `.env.local` для локальной разработки).
2. Пример файла `.env.example` всегда должен быть актуальным и не содержать реальных секретов.
3. Для production рекомендуется использовать Secret Manager (AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager) или GitHub Actions Encrypted Secrets.
4. Для CI/CD:
   - В GitHub Actions использовать secrets для передачи переменных в workflow:
     ```yaml
     env:
       DB_URL: ${{ secrets.DB_URL }}
       JWT_SECRET: ${{ secrets.JWT_SECRET }}
       CANVAS_TOKEN: ${{ secrets.CANVAS_TOKEN }}
     ```
   - Не хранить секреты в репозитории!

### Возможные узкие места и альтернативы:
- **Человеческий фактор**: случайная публикация .env — добавить `.env*` в .gitignore.
- **Масштабируемость**: для multi-env использовать разные файлы `.env.production`, `.env.staging` и переменные окружения в CI/CD.
- **Альтернатива**: для локальной разработки можно использовать dotenv-vault или аналогичные инструменты для шифрования .env.

### Масштабируемость:
- Для production — централизованное хранилище секретов, автоматическая ротация ключей, аудит доступа.

- Для продакшена вынести Canvas LMS, Redis, Elasticsearch и PostgreSQL в отдельные управляемые сервисы (например, AWS RDS, Elasticache, Elastic Cloud).
- Использовать Docker Compose override для production/dev.