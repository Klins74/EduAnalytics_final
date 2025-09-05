import os
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field
from pydantic import ConfigDict

# Явная загрузка .env
env_path = os.getenv('ENV_PATH', None)
if env_path and os.path.exists(env_path):
    print(f"DEBUG: loading env from ENV_PATH={env_path}")
    load_dotenv(env_path)
else:
    print(f"DEBUG: loading env from default .env")
load_dotenv()

# Жестко задаем кодировку клиента для libpq/psycopg2, чтобы исключить влияние текущей кодовой страницы ОС
os.environ.setdefault("PGCLIENTENCODING", "UTF8")

if os.getenv('DEBUG_CONFIG') == '1':
    print(f"DEBUG: os.environ DB_URL = {os.environ.get('DB_URL')}")
    print(f"DEBUG: os.environ DB_URL_SYNC = {os.environ.get('DB_URL_SYNC')}")
    print(f"DEBUG: os.environ DATABASE_URL = {os.environ.get('DATABASE_URL')}")

class Settings(BaseSettings):
    DB_URL: str = Field(default="postgresql+asyncpg://edua:secret@localhost:5432/eduanalytics")
    DB_URL_SYNC: str = Field(default="postgresql+psycopg2://edua:secret@localhost:5432/eduanalytics")
    DATABASE_URL: str = Field(default="postgresql+asyncpg://edua:secret@localhost:5432/eduanalytics")
    N8N_WEBHOOK_URL: str = Field(default="")
    # Новые настройки для расширенной системы уведомлений
    EMAIL_SERVICE_URL: str = Field(default="")
    SMS_SERVICE_URL: str = Field(default="")
    PUSH_SERVICE_URL: str = Field(default="")
    NOTIFICATION_CHANNELS: str = Field(default="webhook,email")  # Разрешенные каналы
    NOTIFICATION_DEFAULT_PRIORITY: str = Field(default="normal")
    # Настройки для email
    SMTP_HOST: str = Field(default="")
    SMTP_PORT: int = Field(default=587)
    SMTP_USERNAME: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    SMTP_USE_TLS: bool = Field(default=True)
    # Настройки для SMS
    SMS_PROVIDER: str = Field(default="")  # twilio, smsc, etc.
    SMS_API_KEY: str = Field(default="")
    SMS_API_SECRET: str = Field(default="")
    # Настройки для push
    PUSH_PROVIDER: str = Field(default="")  # firebase, onesignal, etc.
    PUSH_API_KEY: str = Field(default="")
    PUSH_APP_ID: str = Field(default="")
    CANVAS_TOKEN: str = Field(default="")
    JWT_SECRET: str = Field(default="change_me")
    POSTGRES_USER: str = Field(default="edua")
    POSTGRES_PASSWORD: str = Field(default="secret")
    POSTGRES_DB: str = Field(default="eduanalytics")
    SENTRY_DSN: str = Field(default="https://58714683213474f3dc910effbffda5e3@o4509786424541184.ingest.de.sentry.io/4509786456588368")
    SENTRY_ENVIRONMENT: str = Field(default="development")
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=1.0)
    CANVAS_SECRET_KEY: str = Field(default="")
    CANVAS_LMS_DOMAIN: str = Field(default="localhost")
    CANVAS_LMS_REDIS_URL: str = Field(default="redis://cache:6379/0")
    CANVAS_LMS_ELASTICSEARCH_URL: str = Field(default="http://elasticsearch:9200")
    # Canvas OAuth / API client
    CANVAS_BASE_URL: str = Field(default="")
    CANVAS_CLIENT_ID: str = Field(default="")
    CANVAS_CLIENT_SECRET: str = Field(default="")
    CANVAS_REDIRECT_URI: str = Field(default="")
    CANVAS_RATE_LIMIT: int = Field(default=300)
    REDIS_URL: str = Field(default="redis://cache:6379/0")
    CANVAS_LIVE_EVENTS_SECRET: str = Field(default="")
    CANVAS_EVENTS_STREAM: str = Field(default="canvas:events")
    CANVAS_EVENTS_DLQ: str = Field(default="canvas:events:dlq")
    CANVAS_EVENTS_STREAM_MAXLEN: int = Field(default=10000)
    AI_PROVIDER: str = Field(default="gemini")  # gemini|openrouter|openai|anthropic|ollama
    AI_MODEL: str = Field(default="")
    AI_API_KEY: str = Field(default="")
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = Field(default="gemini-1.5-flash")
    OPENAI_API_KEY: str = Field(default="")
    OPENROUTER_API_KEY: str = Field(default="")
    ANTHROPIC_API_KEY: str = Field(default="")
    OLLAMA_API_BASE: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="tinyllama")
    SUPABASE_URL: str = Field(default="")
    SUPABASE_KEY: str = Field(default="")
    ENABLE_NOTIFICATIONS: bool = Field(default=True)
    DEADLINE_CHECK_ENABLED: bool = Field(default=False)
    DEADLINE_CHECK_INTERVAL: int = Field(default=3600)
    DEADLINE_NOTIFICATION_DAYS: str = Field(default="[7,3,1]")
    # Canvas REST sync runner
    CANVAS_REST_SYNC_ENABLED: bool = Field(default=False)
    CANVAS_REST_SYNC_INTERVAL: int = Field(default=3600)
    CANVAS_SYNC_USER_ID: int = Field(default=0)
    CANVAS_SYNC_SINCE_DAYS: int = Field(default=7)
    CANVAS_DAP_INGEST_ENABLED: bool = Field(default=False)
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(default=None)
    TELEGRAM_TIMEOUT: int = Field(default=30)
    
    # SMS Configuration
    SMS_PROVIDER: str = Field(default="twilio")  # twilio, aws
    SMS_MAX_LENGTH: int = Field(default=160)
    SMS_TIMEOUT: int = Field(default=30)
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID: Optional[str] = Field(default=None)
    TWILIO_AUTH_TOKEN: Optional[str] = Field(default=None)
    TWILIO_FROM_NUMBER: Optional[str] = Field(default=None)
    
    # AWS SMS Configuration
    AWS_REGION: str = Field(default="us-east-1")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None)
    
    # File storage / uploads
    UPLOAD_DIRECTORY: str = Field(default="/app/uploads")
    
    model_config = ConfigDict(extra="allow", env_file=".env", env_file_encoding="utf-8")

    def get_db_url(self, for_migration: bool = False) -> str:
        if for_migration:
            return self.DB_URL_SYNC or self.DATABASE_URL
        return self.DB_URL or self.DATABASE_URL

try:
    settings = Settings()
except Exception as e:
    print(f"WARNING: Failed to load Settings from environment: {e}")
    # Fallback to defaults only
    settings = Settings.model_validate({})