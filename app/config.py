from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "AI Agent Service"
    log_level: str = "INFO"
    # Placeholder for future configuration options
    llm_provider: str = "local"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()