from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import get_settings
from app.schemas.auth import (
    AuthenticatedUserResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth import login_user, register_user
from app.utils.auth import get_current_active_user

router = APIRouter()
settings = get_settings()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    result = login_user(email=payload.email, password=payload.password)
    user = AuthenticatedUserResponse.model_validate(result)
    return TokenResponse(access_token=result["access_token"], user=user)


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest) -> TokenResponse:
    if not settings.allow_self_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-registration is disabled for this deployment.",
        )

    result = register_user(
        full_name=payload.full_name,
        email=payload.email,
        password=payload.password,
        role=payload.role,
    )
    user = AuthenticatedUserResponse.model_validate(result)
    return TokenResponse(access_token=result["access_token"], user=user)


@router.get("/me", response_model=AuthenticatedUserResponse)
def get_me(current_user: dict = Depends(get_current_active_user)) -> AuthenticatedUserResponse:
    return AuthenticatedUserResponse.model_validate(current_user)
