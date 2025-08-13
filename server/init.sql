-- Создание пользователя и базы для Canvas LMS
CREATE USER canvas_user WITH PASSWORD 'password';
CREATE DATABASE canvas;
GRANT ALL PRIVILEGES ON DATABASE canvas TO canvas_user;
-- Остальной код, если нужен, добавить ниже
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'canvas') THEN
        CREATE DATABASE canvas;
    END IF;
END$$;