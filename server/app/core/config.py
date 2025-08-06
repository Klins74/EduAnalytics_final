from pydantic_settings import BaseSettings

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="allow",
        env_file=".env",
        env_file_encoding="utf-8"
    )
    DB_URL: str
    DATABASE_URL: str = None

    def get_db_url(self):
        return self.DB_URL or self.DATABASE_URL
    CANVAS_TOKEN: str
    JWT_SECRET: str

    # --- Notification settings ---
    ENABLE_NOTIFICATIONS: bool = True
    WEBHOOK_URL: str = "http://localhost:5678/webhook/eduanalytics-webhook"
    WEBHOOK_TIMEOUT: int = 10
    DEADLINE_CHECK_ENABLED: bool = True
    DEADLINE_CHECK_INTERVAL: int = 3600
    DEADLINE_NOTIFICATION_DAYS: int = 3

settings = Settings()