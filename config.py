from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "ai-agent"
    log_level: str = "INFO"
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "phi3"

    class Config:
        env_file = ".env"

settings = Settings()