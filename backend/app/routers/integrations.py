from fastapi import APIRouter

from app.schemas.integrations import IntegrationRead
from app.services.integrations import list_integrations

router = APIRouter()


@router.get("/status", response_model=list[IntegrationRead])
def get_integrations_status() -> list[IntegrationRead]:
    return [IntegrationRead.model_validate(item) for item in list_integrations()]
