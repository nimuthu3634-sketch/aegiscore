from pydantic import BaseModel

from app.core.enums import UserRole
from app.schemas.base import ORMModel


class LoginRequest(BaseModel):
    email: str
    password: str


class UserRead(ORMModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
