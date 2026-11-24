from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_is_not_the_plain_password():
    hashed = hash_password("secret123")
    assert hashed != "secret123"


def test_verify_password_accepts_correct_and_rejects_wrong():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed) is True
    assert verify_password("wrongpass", hashed) is False


def test_token_contains_the_user_id():
    token = create_access_token(42)
    assert decode_access_token(token) == 42


def test_invalid_token_returns_none():
    assert decode_access_token("not-a-real-token") is None