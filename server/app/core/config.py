import os
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

print(f"DEBUG: os.environ DB_URL = {os.environ.get('DB_URL')}")
print(f"DEBUG: os.environ DB_URL_SYNC = {os.environ.get('DB_URL_SYNC')}")
print(f"DEBUG: os.environ DATABASE_URL = {os.environ.get('DATABASE_URL')}")

class Settings(BaseSettings):
    DB_URL: str = Field(...)
    DB_URL_SYNC: str = Field(...)
    DATABASE_URL: str = Field(...)
    N8N_WEBHOOK_URL: str = Field(default="")
    CANVAS_TOKEN: str = Field(default="")
    JWT_SECRET: str = Field(...)
    POSTGRES_USER: str = Field(...)
    POSTGRES_PASSWORD: str = Field(...)
    POSTGRES_DB: str = Field(...)
    SENTRY_DSN: str = Field(default="")
    SENTRY_ENVIRONMENT: str = Field(default="development")
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=1.0)
    CANVAS_SECRET_KEY: str = Field(default="")
    CANVAS_LMS_DOMAIN: str = Field(default="localhost")
    CANVAS_LMS_REDIS_URL: str = Field(default="redis://cache:6379/0")
    CANVAS_LMS_ELASTICSEARCH_URL: str = Field(default="http://elasticsearch:9200")
    REDIS_URL: str = Field(default="redis://cache:6379/0")
    AI_API_KEY: str = Field(default="")
    SUPABASE_URL: str = Field(default="")
    SUPABASE_KEY: str = Field(default="")
    model_config = ConfigDict(extra="allow", env_file=".env", env_file_encoding="utf-8")

    def get_db_url(self, for_migration: bool = False) -> str:
        if for_migration:
            return self.DB_URL_SYNC or self.DATABASE_URL
        return self.DB_URL or self.DATABASE_URL

settings = Settings()