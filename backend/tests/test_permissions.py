import pytest

from app.common.exceptions import ForbiddenError
from app.security.permissions import (
    require_administrator,
    require_dentist,
    require_receptionist,
)
from app.security.roles import Role


class _FakeUser:
    def __init__(self, role: Role):
        self.role = role


def test_require_receptionist_allows_receptionist():
    result = _call_dependency(
        require_receptionist,
        _FakeUser(Role.RECEPTIONIST),
    )
    assert result.role == Role.RECEPTIONIST


def test_require_receptionist_blocks_dentist():
    with pytest.raises(ForbiddenError):
        _call_dependency(require_receptionist, _FakeUser(Role.DENTIST))


def test_require_dentist_blocks_receptionist():
    with pytest.raises(ForbiddenError):
        _call_dependency(require_dentist, _FakeUser(Role.RECEPTIONIST))


def test_require_administrator_allows_administrator():
    result = _call_dependency(
        require_administrator,
        _FakeUser(Role.ADMINISTRATOR),
    )
    assert result.role == Role.ADMINISTRATOR


def _call_dependency(dependency_factory, fake_user):
    return dependency_factory(fake_user)

def test_require_administrator_blocks_dentist():
    """Garante que o administrador bloqueia o acesso de dentistas."""
    with pytest.raises(ForbiddenError):
        _call_dependency(require_administrator, _FakeUser(Role.DENTIST))


def test_require_administrator_blocks_receptionist():
    """Garante que o administrador bloqueia o acesso de recepcionistas."""
    with pytest.raises(ForbiddenError):
        _call_dependency(require_administrator, _FakeUser(Role.RECEPTIONIST))


def test_require_dentist_allows_dentist():
    """Garante que o dentista tem acesso às rotas permitidas para sua role."""
    result = _call_dependency(
        require_dentist,
        _FakeUser(Role.DENTIST),
    )
    assert result.role == Role.DENTIST