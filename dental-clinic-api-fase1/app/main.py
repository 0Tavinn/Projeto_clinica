"""
Entry point da API de gestão de clínicas odontológicas.

Fase 1 (fundação): app FastAPI, CORS, tratamento padronizado de erros,
autenticação/RBAC e health check. Demais domínios (pacientes, profissionais,
agendamentos, prontuários, IA) entram em fases seguintes, seguindo a mesma
estrutura modular (routers/schemas/models/repositories/services) já
estabelecida em `app/users`.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.error_handlers import register_exception_handlers
from app.core.config import get_settings
from app.users.router import router as users_router
from app.users.management_router import router as user_management_router
from app.patients.router import router as patients_router

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    debug=settings.DEBUG,
    description=(
        "API de gestão de clínicas odontológicas — MVP acadêmico/profissional. "
        "Consulte o README para o aviso de uso (LGPD, revisão jurídica/segurança "
        "necessária antes de produção)."
    ),
)

# CORS: origens configuráveis por ambiente via CORS_ORIGINS (.env). Em
# development, se vazio, nenhuma origem cross-site é liberada por padrão —
# configure explicitamente conforme necessário.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(user_management_router, prefix=settings.API_V1_PREFIX)
app.include_router(patients_router, prefix=settings.API_V1_PREFIX)

@app.get("/health", tags=["health"], summary="Health check")
def health_check() -> dict:
    """Endpoint simples de liveness, sem dependência de banco (Fase 1)."""
    return {"status": "ok", "app": settings.APP_NAME, "environment": settings.ENVIRONMENT}
