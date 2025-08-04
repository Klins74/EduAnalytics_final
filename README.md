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