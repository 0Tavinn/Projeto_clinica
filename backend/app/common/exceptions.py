"""
Exceções de domínio/aplicação.

Estas exceções são levantadas pelas camadas de service/repository e NÃO
conhecem HTTP. A tradução para respostas HTTP acontece em
`app.common.error_handlers`, mantendo a lógica de negócio desacoplada do
framework web.
"""


class AppError(Exception):
    """Classe base para todos os erros de aplicação conhecidos."""

    default_message = "Erro inesperado na aplicação."

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundError(AppError):
    default_message = "Recurso não encontrado."


class ConflictError(AppError):
    """Ex.: conflito de horário de agenda, violação de unicidade, etc."""

    default_message = "Conflito ao processar a operação."


class ValidationAppError(AppError):
    """Erros de validação de regra de negócio (não de schema/Pydantic)."""

    default_message = "Dados inválidos para esta operação."


class UnauthorizedError(AppError):
    """Credenciais ausentes ou inválidas."""

    default_message = "Não autenticado."


class ForbiddenError(AppError):
    """Usuário autenticado, mas sem permissão para o recurso/ação."""

    default_message = "Acesso não autorizado a este recurso."


class InactiveUserError(UnauthorizedError):
    default_message = "Usuário inativo."
