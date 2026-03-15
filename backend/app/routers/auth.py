from fastapi import APIRouter, Depends

from app.core.security import get_token_payload
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserRead
from app.services.auth import (
    get_current_user_from_payload,
    login_user,
    register_user,
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    result = login_user(email=payload.email, password=payload.password)
    user = UserRead.model_validate(result)
    return TokenResponse(access_token=result["access_token"], user=user)


@router.post("/register", response_model=UserRead)
def register(payload: RegisterRequest) -> UserRead:
    user = register_user(
        full_name=payload.full_name,
        email=payload.email,
        password=payload.password,
        role=payload.role,
    )
    return UserRead.model_validate(user)


@router.get("/me", response_model=UserRead)
def get_me(token_payload: dict = Depends(get_token_payload)) -> UserRead:
    user = get_current_user_from_payload(token_payload)
    return UserRead.model_validate(user)
