"""
Tratamento padronizado de erros da API.

Todas as respostas de erro seguem o formato:

    {
      "error": {
        "code": "NOT_FOUND",
        "message": "...",
        "details": null
      }
    }

Isso dá ao front-end (ou a qualquer client HTTP/JS puro) um contrato único
e previsível para tratar erros, independente da camada que os gerou.
"""
import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    InactiveUserError,
    NotFoundError,
    UnauthorizedError,
    ValidationAppError,
)
from app.security.rate_limit import RateLimitExceededError

# Logger dedicado a erros da API. IMPORTANTE: nunca logar senha, token ou
# conteúdo clínico aqui — apenas metadados da requisição/erro.
logger = logging.getLogger("dental_clinic_api.errors")

_ERROR_STATUS_MAP: dict[type[AppError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    ValidationAppError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    UnauthorizedError: status.HTTP_401_UNAUTHORIZED,
    InactiveUserError: status.HTTP_401_UNAUTHORIZED,
    ForbiddenError: status.HTTP_403_FORBIDDEN,
    RateLimitExceededError: status.HTTP_429_TOO_MANY_REQUESTS,
}


def _error_body(code: str, message: str, details=None) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


def _status_for(exc: AppError) -> int:
    for exc_type, http_status in _ERROR_STATUS_MAP.items():
        if isinstance(exc, exc_type):
            return http_status
    return status.HTTP_400_BAD_REQUEST


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        http_status = _status_for(exc)
        logger.warning(
            "app_error path=%s method=%s type=%s status=%s",
            request.url.path,
            request.method,
            type(exc).__name__,
            http_status,
        )
        headers = {"WWW-Authenticate": "Bearer"} if http_status == 401 else None
        return JSONResponse(
            status_code=http_status,
            content=_error_body(type(exc).__name__.upper(), exc.message),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Erros de validação do Pydantic (schema/entrada). Não logamos o
        # corpo cru da requisição para evitar vazar dados sensíveis em logs.
        logger.info(
            "validation_error path=%s method=%s errors=%s",
            request.url.path,
            request.method,
            exc.errors(),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body(
                "VALIDATION_ERROR", "Dados de entrada inválidos.", exc.errors()
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(
                "HTTP_ERROR", str(exc.detail) if exc.detail else "Erro HTTP."
            ),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        # Falha inesperada: nunca vaza detalhes internos para o client.
        logger.exception(
            "unhandled_exception path=%s method=%s", request.url.path, request.method
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body(
                "INTERNAL_ERROR", "Erro interno. Tente novamente mais tarde."
            ),
        )
