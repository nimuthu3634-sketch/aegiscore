from datetime import datetime

from pydantic import BaseModel

from app.core.enums import UserRole
from app.schemas.base import ORMModel


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    role: UserRole = UserRole.VIEWER


class UserRead(ORMModel):
    id: str
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime


class AuthenticatedUserResponse(UserRead):
    pass


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthenticatedUserResponse
