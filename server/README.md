# EduAnalytics Backend

## 📌 Database: Alembic Migrations

### Alembic Setup & Usage

1. **Initialize Alembic (already done):**
   ```bash
   alembic init migrations
   ```
2. **Configure DB URL:**
   - DB URL is loaded from `.env` via `app.core.config` (do not hardcode in alembic.ini).
3. **Create Migration:**
   ```bash
   alembic revision --autogenerate -m "Initial migration"
   ```
4. **Apply Migration:**
   ```bash
   alembic upgrade head
   ```
5. **Best Practices:**
   - Всегда используйте переменные окружения для подключения к БД.
   - Для автогенерации миграций импортируйте Base из `app.db.base`.
   - Для новых моделей — пересоздайте миграцию и примените upgrade.