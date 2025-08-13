# /server/Dockerfile

# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код из папки server в контейнер
COPY . .

# Сообщаем Docker, что контейнер будет слушать порт 8000
EXPOSE 8000

# Команда для запуска приложения (будет перезаписана в docker-compose.yml для режима разработки)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

ENV PYTHONPATH=/app