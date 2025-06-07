from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Manages application settings and loads them from a .env file.
    """
    DEEPGRAM_API_KEY: str
    GROQ_API_KEY: str
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=True
    )

# Create a single, reusable instance of the settings
settings = Settings()