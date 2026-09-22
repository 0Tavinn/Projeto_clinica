"""Perfis de acesso da aplicação."""

import enum


class Role(str, enum.Enum):
    ADMINISTRATOR = "ADMINISTRATOR"
    RECEPTIONIST = "RECEPTIONIST"
    DENTIST = "DENTIST"


# Os três perfis previstos para a Sprint 3 estão habilitados.
MVP_ACTIVE_ROLES: frozenset[Role] = frozenset(Role)