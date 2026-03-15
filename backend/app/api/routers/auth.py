from fastapi import APIRouter

from app.schemas.auth import LoginRequest, TokenResponse, UserRead
from app.services.auth import list_demo_users, login_user

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    result = login_user(email=payload.email, password=payload.password)
    user = UserRead.model_validate(result)
    return TokenResponse(access_token=result["access_token"], user=user)


@router.get("/users", response_model=list[UserRead])
def get_demo_users() -> list[UserRead]:
    return [UserRead.model_validate(user) for user in list_demo_users()]
