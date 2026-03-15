from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    version: str
    database: str
    redis: str


class MessageResponse(BaseModel):
    message: str
