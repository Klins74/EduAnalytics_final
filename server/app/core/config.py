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
    N8N_WEBHOOK_URL: str = None
    def get_db_url(self):
        return self.DB_URL or self.DATABASE_URL
    CANVAS_TOKEN: str
    JWT_SECRET: str



settings = Settings()