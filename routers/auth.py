from schemas.auth import TokenResponse, LoginRequest
from handlers.auth import check_password, generate_jwt
from config import settings
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    if not check_password(body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return TokenResponse(
        access_token=generate_jwt(),
        token_type="bearer",
        expires_in=settings.SIEM_JWT_TTL_SECONDS,
    )
