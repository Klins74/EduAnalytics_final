# EduAnalytics Environment Variables

Этот файл описывает все переменные окружения, используемые в проекте EduAnalytics.

## Создание .env файла

1. Скопируйте этот шаблон в файл `.env` в корне проекта
2. Обновите значения для вашей среды
3. **Никогда не коммитьте .env файл в git!**

## Переменные окружения

### База данных

```env
# Основная база данных для EduAnalytics API
POSTGRES_USER=edua
POSTGRES_PASSWORD=secret
POSTGRES_DB=eduanalytics

# URL подключений (автоматически формируются из POSTGRES_*)
DB_URL=postgresql+asyncpg://edua:secret@localhost:5432/eduanalytics
DB_URL_SYNC=postgresql+psycopg2://edua:secret@localhost:5432/eduanalytics
DATABASE_URL=postgresql+asyncpg://edua:secret@localhost:5432/eduanalytics

# Исправление проблем с кодировкой в Windows
PGCLIENTENCODING=UTF8
```

### Аутентификация и безопасность

```env
# Секретный ключ для JWT токенов (сгенерируйте: openssl rand -hex 32)
JWT_SECRET=your-super-secret-jwt-key-here-change-this-in-production
SECRET_KEY=your-super-secret-jwt-key-here-change-this-in-production

# Настройки администратора (создается автоматически)
ADMIN_USERNAME=admin@eduanalytics.local
ADMIN_PASSWORD=change-this-secure-password
ADMIN_EMAIL=admin@eduanalytics.local
```

### AI Configuration

```env
# Выберите провайдера: gemini, openai, openrouter, ollama
AI_PROVIDER=gemini

# Google Gemini
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-1.5-flash

# OpenAI
OPENAI_API_KEY=your-openai-api-key-here

# OpenRouter
OPENROUTER_API_KEY=your-openrouter-api-key-here

# Anthropic Claude
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Ollama (локальный, бесплатный)
OLLAMA_API_BASE=http://localhost:11434
OLLAMA_MODEL=tinyllama
```

### Система уведомлений

```env
# n8n webhook URLs
N8N_WEBHOOK_URL=http://localhost:5678/webhook/eduanalytics
EMAIL_SERVICE_URL=http://localhost:5678/webhook/email
SMS_SERVICE_URL=http://localhost:5678/webhook/sms
PUSH_SERVICE_URL=http://localhost:5678/webhook/push
```

### Проверка дедлайнов

```env
# Включить автоматическую проверку дедлайнов
DEADLINE_CHECK_ENABLED=true
# Интервал проверки в секундах (3600 = 1 час)
DEADLINE_CHECK_INTERVAL=3600
# Дни до дедлайна для уведомлений (через запятую)
DEADLINE_NOTIFICATION_DAYS=7,3,1
```

### Мониторинг

```env
# Sentry для отслеживания ошибок
SENTRY_DSN=your-sentry-dsn-here
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=1.0
SENTRY_PROFILES_SAMPLE_RATE=0.0

# Логирование
LOG_LEVEL=INFO
LOG_FILE_PATH=notifications.log
```

### Canvas LMS (опционально)

```env
# Интеграция с Canvas
CANVAS_TOKEN=your-canvas-token-here
CANVAS_BASE_URL=https://your-canvas-instance.instructure.com
CANVAS_SECRET_KEY=your-canvas-secret-key-here

# Canvas использует отдельную БД
CANVAS_LMS_POSTGRES_USER=user
CANVAS_LMS_POSTGRES_PASSWORD=password
CANVAS_LMS_POSTGRES_DB=canvas
```

### Redis

```env
# URL для подключения к Redis
REDIS_URL=redis://localhost:6379
```

### CORS (для продакшена)

```env
# Разрешенные домены (через запятую)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:4028
```

## Пример .env файла для разработки

```env
# Database
POSTGRES_USER=edua
POSTGRES_PASSWORD=secret
POSTGRES_DB=eduanalytics
PGCLIENTENCODING=UTF8

# Auth
JWT_SECRET=dev-secret-key-change-in-production
SECRET_KEY=dev-secret-key-change-in-production

# Admin
ADMIN_USERNAME=admin@dev.local
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@dev.local

# AI
AI_PROVIDER=ollama
OLLAMA_API_BASE=http://localhost:11434
OLLAMA_MODEL=tinyllama

# Notifications
N8N_WEBHOOK_URL=http://localhost:5678/webhook/eduanalytics
DEADLINE_CHECK_ENABLED=true
DEADLINE_CHECK_INTERVAL=3600

# Monitoring
LOG_LEVEL=DEBUG
SENTRY_ENVIRONMENT=development
```

## Пример .env файла для продакшена

```env
# Database (используйте реальные учетные данные)
POSTGRES_USER=eduanalytics_prod
POSTGRES_PASSWORD=very-secure-password-here
POSTGRES_DB=eduanalytics_prod
PGCLIENTENCODING=UTF8

# Auth (сгенерируйте надежные ключи)
JWT_SECRET=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
SECRET_KEY=z6y5x4w3v2u1t0s9r8q7p6o5n4m3l2k1j0i9h8g7f6e5d4c3b2a1

# Admin
ADMIN_USERNAME=admin@yourdomain.com
ADMIN_PASSWORD=very-secure-admin-password
ADMIN_EMAIL=admin@yourdomain.com

# AI (используйте продакшен ключи)
AI_PROVIDER=gemini
GEMINI_API_KEY=your-real-gemini-api-key
GEMINI_MODEL=gemini-1.5-flash

# Notifications (реальные URL сервисов)
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/eduanalytics
EMAIL_SERVICE_URL=https://your-email-service.com/send
DEADLINE_CHECK_ENABLED=true
DEADLINE_CHECK_INTERVAL=1800

# Monitoring
LOG_LEVEL=INFO
SENTRY_DSN=https://your-real-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# CORS
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

## Troubleshooting

### Проблемы с кодировкой в Windows

Если получаете ошибку `UnicodeDecodeError`, убедитесь что:

1. `PGCLIENTENCODING=UTF8` установлена
2. Файл .env сохранен в кодировке UTF-8 без BOM
3. В PowerShell выполните: `chcp 65001`

### Проблемы с подключением к базе данных

1. Убедитесь что PostgreSQL запущен
2. Проверьте учетные данные
3. Для Docker: используйте `db` вместо `localhost` в URL
4. Для локальной разработки: используйте `localhost`

