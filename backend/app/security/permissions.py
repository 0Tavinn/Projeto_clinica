"""Controle de acesso baseado nos perfis de usuário."""
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
                "Este perfil não está habilitado nesta fase da API."
            )

        if current_user.role not in allowed_roles:
            raise ForbiddenError(
                "Usuário não tem permissão para acessar este recurso."
            )

        return current_user

    return _dependency


require_administrator = require_roles(Role.ADMINISTRATOR)
require_receptionist = require_roles(Role.RECEPTIONIST)
require_dentist = require_roles(Role.DENTIST)
require_any_staff = require_roles(
    Role.ADMINISTRATOR,
    Role.RECEPTIONIST,
    Role.DENTIST,
)

# Administrador e recepcionista podem inativar pacientes.
require_patient_manager = require_roles(
    Role.ADMINISTRATOR,
    Role.RECEPTIONIST,
)

# Administrador, recepcionista e dentista podem cadastrar e editar pacientes.
require_patient_editor = require_roles(
    Role.ADMINISTRATOR,
    Role.RECEPTIONIST,
    Role.DENTIST,
)