"""
Configurações centrais da aplicação.

Todas as configurações sensíveis (segredos, credenciais, URLs de banco) DEVEM
vir exclusivamente de variáveis de ambiente. Nunca hardcode segredos aqui.
"""
from functools import lru_cache
from typing import Annotated, List, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """
    Settings da aplicação, carregadas de variáveis de ambiente (ou de um
    arquivo .env em desenvolvimento). Ver .env.example para a lista completa
    de variáveis suportadas.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Ambiente -----------------------------------------------------
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    APP_NAME: str = "Dental Clinic API"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Exemplo PostgreSQL:
    # postgresql+psycopg://user:password@host:5432/database
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://clinic_app:change_me@127.0.0.1:5432/clinic_management",
    )

    # --- Segurança / JWT --------------------------------------------------
    # OBRIGATÓRIO definir via variável de ambiente em qualquer ambiente
    # real. O default aqui só existe para não quebrar `import` acidental;
    # é validado/rejeitado fora de development mais abaixo.
    SECRET_KEY: str = Field(default="INSECURE-DEV-ONLY-CHANGE-ME")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 dias

    # --- CORS ---------------------------------------------------------
    # Aceita string separada por vírgula via env var (ex.: CORS_ORIGINS=
    # http://localhost:3000,http://localhost:5173). NoDecode evita que o
    # pydantic-settings tente fazer parse como JSON antes do validador
    # abaixo rodar (o que quebraria em valores vazios ou não-JSON).
    CORS_ORIGINS: Annotated[List[str], NoDecode] = Field(default_factory=list)

    # --- Rate limiting (usado pelos endpoints sensíveis) -----------------
    LOGIN_RATE_LIMIT: str = "5/minute"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return []
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def _validate_secret_key(cls, v: str, info):
        # Em produção, recusamos subir com o segredo default inseguro.
        # (A checagem completa contra ENVIRONMENT é feita em get_settings,
        # pois a ordem de validação de campos não é garantida.)
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.is_production and settings.SECRET_KEY == "INSECURE-DEV-ONLY-CHANGE-ME":
        raise RuntimeError(
            "SECRET_KEY inseguro (default) detectado em ambiente de produção. "
            "Defina a variável de ambiente SECRET_KEY com um valor forte e único."
        )
    return settings
