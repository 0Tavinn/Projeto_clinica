from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Lumina Odonto API"
    environment: str = "development"
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    clinical_token_minutes: int = 15
    opencl_default_engine: str = "auto"
    opencl_max_text_bytes: int = 2_000_000
    opencl_max_term_chars: int = 128
    cors_origins: str = "http://localhost:3000"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
