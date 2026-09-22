"""Hash e verificação de senhas usando Argon2 (via passlib)."""
from passlib.context import CryptContext

# Argon2 é o algoritmo recomendado atualmente (vencedor da Password Hashing
# Competition) e é a escolha primária pedida no escopo. bcrypt fica como
# fallback de verificação, caso hashes legados existam no futuro.
_pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return _pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        # Hash em formato desconhecido/corrompido — trata como inválido em
        # vez de propagar exceção (evita vazar detalhes de implementação).
        return False
