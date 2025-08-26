# EduAnalytics - Canvas LMS совместимая платформа

Современная образовательная платформа, построенная на архитектуре Canvas LMS с использованием современного стека технологий.

## 🚀 Основные возможности

### 📚 Canvas LMS совместимость
- **Quiz Engine** - полнофункциональная система тестирования
- **Pages** - создание и управление материалами курса
- **Discussions** - форумы и обсуждения
- **Modules** - организация контента по модулям
- **Assignment Groups** - группы заданий
- **Rubrics** - критерии оценивания

### 🤖 AI интеграция
- **Ollama** - локальная AI модель для обработки запросов
- **Intent Extraction** - извлечение намерений из пользовательских запросов
- **Function Calling** - вызов API функций через AI
- **AI-powered Analytics** - аналитика с использованием AI

### 🎨 Современный UI/UX
- **Responsive Design** - адаптивный дизайн для всех устройств
- **Rich Markdown Editor** - редактор с подсветкой синтаксиса
- **Search & Filter** - продвинутый поиск и фильтрация
- **Content Statistics** - визуализация статистики
- **Notification System** - система уведомлений
- **Confirmation Dialogs** - диалоги подтверждения

## 🛠 Технический стек

### Backend
- **FastAPI** - современный веб-фреймворк
- **SQLAlchemy** - ORM для работы с базой данных
- **PostgreSQL** - основная база данных
- **Redis** - кэширование и очереди
- **Alembic** - миграции базы данных
- **Docker** - контейнеризация

### Frontend
- **React 18** - современная библиотека UI
- **Tailwind CSS** - utility-first CSS фреймворк
- **React Router** - маршрутизация
- **Custom Hooks** - переиспользуемая логика

### AI & ML
- **Ollama** - локальная LLM
- **Google Gemini** - облачная AI модель
- **OpenRouter** - API для различных AI моделей

## 📁 Структура проекта

```
EduAnalytics/
├── server/                 # Backend
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Конфигурация и безопасность
│   │   ├── crud/          # CRUD операции
│   │   ├── models/        # SQLAlchemy модели
│   │   ├── schemas/       # Pydantic схемы
│   │   └── services/      # Бизнес-логика
│   ├── migrations/        # Миграции базы данных
│   └── docker-compose.yml # Docker конфигурация
├── src/                    # Frontend
│   ├── components/        # React компоненты
│   │   └── ui/           # UI компоненты
│   ├── pages/            # Страницы приложения
│   ├── api/              # API клиенты
│   └── utils/            # Утилиты
└── public/                # Статические файлы
```

## 🚀 Быстрый старт

### 1. Клонирование репозитория
```bash
git clone https://github.com/your-username/EduAnalytics.git
cd EduAnalytics
```

### 2. Запуск с Docker
```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f api
```

### 3. Запуск Frontend
```bash
cd src
npm install
npm run dev
```

### 4. Доступ к приложению
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Ollama**: http://localhost:11434
- **Database**: localhost:5432

## 🔧 Конфигурация

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/eduanalytics

# AI Providers
# выберите один из провайдеров: gemini | openrouter | ollama
AI_PROVIDER=gemini

# Gemini
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-1.5-flash

# OpenRouter (альтернатива Gemini)
OPENROUTER_API_KEY=your_openrouter_key
AI_MODEL=openrouter/auto

# Ollama (локальный провайдер)
OLLAMA_API_BASE=http://ollama:11434
OLLAMA_MODEL=tinyllama

# Security
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Docker Services
- **api** - FastAPI приложение
- **db** - PostgreSQL база данных
- **redis** - Redis кэш
- **ollama** - Локальная AI модель

## 📊 API Endpoints

### Authentication
- `POST /api/auth/token` - Получение JWT токена
- `POST /api/auth/refresh` - Обновление токена

### Quiz Engine
- `GET /api/quizzes` - Список квизов
- `POST /api/quizzes` - Создание квиза
- `GET /api/quizzes/{id}` - Получение квиза
- `PUT /api/quizzes/{id}` - Обновление квиза
- `DELETE /api/quizzes/{id}` - Удаление квиза

### Pages
- `GET /api/pages/course/{course_id}` - Страницы курса
- `POST /api/pages` - Создание страницы
- `PUT /api/pages/{id}` - Обновление страницы
- `DELETE /api/pages/{id}` - Удаление страницы

### Discussions
- `GET /api/discussions/course/{course_id}` - Темы курса
- `POST /api/discussions` - Создание темы
- `POST /api/discussions/{id}/entries` - Добавление сообщения

### AI Services
- `POST /api/ai/chat` - AI чат
- `POST /api/ai/chat/stream` - Стриминг AI ответов
- `POST /api/ai/intent` - Извлечение намерений
- `POST /api/ai/function` - Вызов функций

## 🎯 Основные функции

### Quiz Engine
- Создание различных типов вопросов
- Автоматическое оценивание
- AI-powered обратная связь
- Статистика прохождения

### Content Management
- Rich text редактор с Markdown
- Организация по модулям
- Версионирование контента
- Поиск и фильтрация

### Discussion System
- Треды и ответы
- Модерация контента
- Уведомления о новых сообщениях
- Интеграция с модулями

### Analytics Dashboard
- Статистика по курсам
- Прогресс студентов
- AI-powered рекомендации
- Экспорт отчетов

## 🔒 Безопасность

- **JWT Authentication** - безопасная аутентификация
- **RBAC** - ролевая модель доступа
- **Input Validation** - валидация входных данных
- **SQL Injection Protection** - защита от SQL инъекций
- **CORS** - настройки безопасности браузера

## 📈 Производительность

- **Async/Await** - асинхронная обработка запросов
- **Database Indexing** - оптимизация запросов
- **Redis Caching** - кэширование данных
- **Connection Pooling** - пул соединений с БД
- **Lazy Loading** - ленивая загрузка данных

## 🧪 Тестирование

### Backend Tests
```bash
cd server
pytest tests/ -v
```

### Frontend Tests
```bash
cd src
npm test
```

### API Tests
```bash
# Тестирование Quiz Engine
curl -X GET "http://localhost:8000/api/quizzes" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Тестирование AI
curl -X POST "http://localhost:8000/api/ai/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "Привет, как дела?"}'
```

## 🚀 Развертывание

### Production
```bash
# Сборка production образа
docker build -t eduanalytics:prod .

# Запуск production
docker-compose -f docker-compose.prod.yml up -d
```

### Staging
```bash
# Развертывание на staging сервере
docker-compose -f docker-compose.staging.yml up -d
```

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📝 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 🙏 Благодарности

- **Canvas LMS** - за архитектурные решения
- **FastAPI** - за отличный веб-фреймворк
- **React Team** - за современную UI библиотеку
- **Tailwind CSS** - за utility-first подход

## 📞 Поддержка

- **Issues**: [GitHub Issues](https://github.com/your-username/EduAnalytics/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/EduAnalytics/discussions)
- **Email**: support@eduanalytics.com

---

**EduAnalytics** - современная образовательная платформа для будущего обучения! 🎓✨