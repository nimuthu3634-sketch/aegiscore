from fastapi import APIRouter, Depends

from app.schemas.incidents import IncidentRead
from app.services.incidents import list_incidents
from app.utils.auth import get_current_active_user

router = APIRouter()


@router.get("", response_model=list[IncidentRead])
def get_incidents(current_user: dict = Depends(get_current_active_user)) -> list[IncidentRead]:
    return [IncidentRead.model_validate(incident) for incident in list_incidents()]
