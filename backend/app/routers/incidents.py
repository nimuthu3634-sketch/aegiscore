from fastapi import APIRouter

from app.schemas.incidents import IncidentRead
from app.services.incidents import list_incidents

router = APIRouter()


@router.get("", response_model=list[IncidentRead])
def get_incidents() -> list[IncidentRead]:
    return [IncidentRead.model_validate(incident) for incident in list_incidents()]
