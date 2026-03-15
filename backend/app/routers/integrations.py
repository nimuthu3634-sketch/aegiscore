from fastapi import APIRouter, Depends

from app.schemas.integrations import IntegrationRead
from app.services.integrations import list_integrations
from app.utils.auth import get_current_active_user

router = APIRouter()


@router.get("/status", response_model=list[IntegrationRead])
def get_integrations_status(
    current_user: dict = Depends(get_current_active_user),
) -> list[IntegrationRead]:
    return [IntegrationRead.model_validate(item) for item in list_integrations()]
