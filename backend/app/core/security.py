from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    return password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(user_id: int) -> str:
    expire_time = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": str(user_id), "exp": expire_time}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)