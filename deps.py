from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from config import settings

_http_bearer = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_admin(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer)],
) -> None:
    if credentials is None:
        raise _unauthorized()

    if credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token, settings.SIEM_JWT_SECRET, algorithms=[settings.SIEM_JWT_ALG]
        )

    except JWTError:
        raise _unauthorized()

    if payload.get("sub") != "admin":
        raise _unauthorized()
