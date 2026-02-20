from jose import jwt

from datetime import datetime, timezone, timedelta
import bcrypt
from config import settings


def check_password(plain_password: str) -> bool:
    if len(plain_password.encode("utf-8")) > 72:
        return False
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        settings.SIEM_ADMIN_PASSWORD_HASH.encode("utf-8"),
    )


def generate_jwt() -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(seconds=settings.SIEM_JWT_TTL_SECONDS)

    payload = {
        "sub": "admin",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    return jwt.encode(
        payload, settings.SIEM_JWT_SECRET, algorithm=settings.SIEM_JWT_ALG
    )
