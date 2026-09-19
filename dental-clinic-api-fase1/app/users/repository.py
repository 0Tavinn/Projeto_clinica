"""Camada de acesso a dados para usuários."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.users.models import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int | str) -> User | None:
        try:
            return self.db.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.lower())
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_cpf(self, cpf: str) -> User | None:
        statement = select(User).where(User.cpf == cpf)
        return self.db.execute(statement).scalar_one_or_none()

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user