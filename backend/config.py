from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Model Configuration
    MODEL_PATH: str = "./YuFeng-XGuard-Reason-0.6B"
    DEVICE: str = "auto"

    # Upstream LLM Configuration (For Proxy)
    UPSTREAM_API_BASE: str = "https://api.openai.com/v1"
    UPSTREAM_API_KEY: str = "sk-placeholder"
    UPSTREAM_MODEL: str = "gpt-3.5-turbo"

    class Config:
        env_file = ".env"

settings = Settings()
