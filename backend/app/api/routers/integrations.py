from fastapi import APIRouter

from app.schemas.integrations import IntegrationRead
from app.services.integrations import list_integrations

router = APIRouter()


@router.get("", response_model=list[IntegrationRead])
def get_integrations() -> list[IntegrationRead]:
    return [IntegrationRead.model_validate(integration) for integration in list_integrations()]
