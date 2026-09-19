from app.security.hashing import hash_password, verify_password


def test_hash_password_produces_argon2_hash():
    hashed = hash_password("Senha@1234")
    assert hashed != "Senha@1234"
    assert hashed.startswith("$argon2")


def test_verify_password_correct():
    hashed = hash_password("Senha@1234")
    assert verify_password("Senha@1234", hashed) is True


def test_verify_password_incorrect():
    hashed = hash_password("Senha@1234")
    assert verify_password("outra-senha", hashed) is False


def test_verify_password_with_malformed_hash_does_not_raise():
    assert verify_password("Senha@1234", "isso-nao-e-um-hash-valido") is False
