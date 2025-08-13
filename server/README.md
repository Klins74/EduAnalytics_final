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
   - **Идемпотентные миграции:** Все операции с constraint/column должны быть защищены проверкой существования через SQL-запросы к information_schema. Это позволяет безопасно повторять миграции и избегать ошибок DuplicateObject/UndefinedObject.
   - **Пример проверки существования constraint:**
     ```python
     constraint_exists = conn.execute(sa.text("""
         SELECT 1 FROM information_schema.table_constraints
         WHERE constraint_name = 'fk_grades_student_id_students' AND table_name = 'grades'
     """)).scalar() is not None
     if constraint_exists:
         batch_op.drop_constraint('fk_grades_student_id_students', type_='foreignkey')
     ```
   - **Пример проверки существования колонки:**
     ```python
     column_exists = conn.execute(sa.text("""
         SELECT 1 FROM information_schema.columns
         WHERE table_name = 'grades' AND column_name = 'student_id'
     """)).scalar() is not None
     if column_exists:
         batch_op.drop_column('student_id')
     ```
   - **Рекомендации:**
     - Все миграции должны быть идемпотентными (безопасны для повторного запуска).
     - Используйте batch_alter_table для совместимости с SQLite.
     - Документируйте логику проверки в каждом ревизионном файле.

## 🗄️ Инициализация PostgreSQL для Canvas LMS

### Шаги для локального и CI-setup

1. При первом запуске контейнера `db` автоматически создаются пользователи и базы:
   - Пользователь: `canvas_user` (пароль: `password`)
   - Базы: `eduanalytics`, `canvas`
2. Если требуется ручная инициализация:
   - Подключитесь к контейнеру:
     ```bash
     docker-compose exec db psql -U edua -d eduanalytics
     ```
   - Выполните SQL:
     ```sql
     CREATE USER canvas_user WITH PASSWORD 'password';
     CREATE DATABASE canvas;
     GRANT ALL PRIVILEGES ON DATABASE canvas TO canvas_user;
     ```
3. Проверьте переменные окружения:
   - В `docker-compose.yml` и `.env` используйте:
     - `CANVAS_LMS_POSTGRES_USER=canvas_user`
     - `CANVAS_LMS_POSTGRES_PASSWORD=password`
     - `DB_URL=postgresql+asyncpg://canvas_user:password@db:5432/eduanalytics`
4. Для CI/CD убедитесь, что init.sql монтируется в `docker-entrypoint-initdb.d/`.

### Troubleshooting
- Ошибка `role "user" does not exist` — проверьте, что Canvas LMS использует `canvas_user`.
- Ошибка `database "canvas" does not exist` — убедитесь, что база создана через init.sql или вручную.