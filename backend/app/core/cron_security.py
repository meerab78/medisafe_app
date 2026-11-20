import secrets

from fastapi import Header, HTTPException

from app.core.config import settings


def verify_cron_secret(x_cron_secret: str | None = Header(default=None)):
    # If no secret is set on the server, the endpoint stays locked
    if not settings.cron_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if x_cron_secret is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # compare_digest compares in constant time, which is safer than ==
    is_same = secrets.compare_digest(
        x_cron_secret.encode(), settings.cron_secret.encode()
    )
    if not is_same:
        raise HTTPException(status_code=401, detail="Unauthorized")