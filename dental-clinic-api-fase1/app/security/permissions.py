"""
RBAC — controle de acesso por perfil (role).

Uso típico em um router:

    @router.get("/patients", dependencies=[Depends(require_roles(Role.RECEPTIONIST))])
    def list_patients(...): ...

ou, quando o handler também precisa do usuário atual:

    def list_patients(current_user: Annotated[User, Depends(require_roles(Role.RECEPTIONIST))]):
        ...

`require_roles` sempre valida, além do perfil solicitado, se o perfil está
entre os habilitados no MVP (`MVP_ACTIVE_ROLES`) — isso impede que um
usuário PATIENT/ADMIN "vazado" no banco (ex.: dado de fase 2 sendo
preparado) acesse endpoints do MVP por engano de configuração.
"""
from typing import Annotated

from fastapi import Depends

from app.common.exceptions import ForbiddenError
from app.security.auth import CurrentUser
from app.security.roles import MVP_ACTIVE_ROLES, Role
from app.users.models import User


def require_roles(*allowed_roles: Role):
    if not allowed_roles:
        raise ValueError("require_roles precisa de ao menos um Role.")

    def _dependency(current_user: CurrentUser) -> User:
        if current_user.role not in MVP_ACTIVE_ROLES:
            raise ForbiddenError(
                "Este perfil ainda não está habilitado nesta fase da API."
            )
        if current_user.role not in allowed_roles:
            raise ForbiddenError(
                "Usuário não tem permissão para acessar este recurso."
            )
        return current_user

    return _dependency


# Atalhos comuns para os dois perfis ativos no MVP.
require_receptionist = require_roles(Role.RECEPTIONIST)
require_dentist = require_roles(Role.DENTIST)
require_any_staff = require_roles(Role.RECEPTIONIST, Role.DENTIST)
