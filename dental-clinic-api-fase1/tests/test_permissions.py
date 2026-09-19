import pytest

from app.common.exceptions import ForbiddenError
from app.security.permissions import require_dentist, require_receptionist
from app.security.roles import Role


class _FakeUser:
    def __init__(self, role: Role):
        self.role = role


def test_require_receptionist_allows_receptionist():
    result = _call_dependency(require_receptionist, _FakeUser(Role.RECEPTIONIST))
    assert result.role == Role.RECEPTIONIST


def test_require_receptionist_blocks_dentist():
    with pytest.raises(ForbiddenError):
        _call_dependency(require_receptionist, _FakeUser(Role.DENTIST))


def test_require_dentist_blocks_receptionist():
    with pytest.raises(ForbiddenError):
        _call_dependency(require_dentist, _FakeUser(Role.RECEPTIONIST))


def test_mvp_inactive_role_is_always_blocked_even_if_listed():
    """
    PATIENT/ADMIN não estão em MVP_ACTIVE_ROLES: mesmo que um endpoint
    futuro liste Role.PATIENT em require_roles por engano, o acesso deve
    ser negado nesta fase.
    """
    from app.security.permissions import require_roles

    dependency_allowing_patient = require_roles(Role.PATIENT)
    with pytest.raises(ForbiddenError):
        _call_dependency(dependency_allowing_patient, _FakeUser(Role.PATIENT))


def _call_dependency(dependency_factory, fake_user):
    # `require_roles(...)` retorna uma closure `_dependency(current_user)`.
    # Chamamos diretamente, sem passar pelo FastAPI/Depends, para testar a
    # lógica de RBAC de forma isolada e rápida.
    return dependency_factory(fake_user)
