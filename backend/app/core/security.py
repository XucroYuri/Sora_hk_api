from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings

_security = HTTPBearer(auto_error=False)


def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> None:
    if not settings.AUTH_TOKEN:
        return

    if not credentials or credentials.credentials != settings.AUTH_TOKEN:
        raise HTTPException(
            status_code=401,
            detail={"code": "unauthorized", "message": "Authentication required"},
            headers={"WWW-Authenticate": "Bearer"},
        )
