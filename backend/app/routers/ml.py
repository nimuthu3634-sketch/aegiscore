from fastapi import APIRouter, Depends

from app.core.enums import UserRole
from app.schemas.ml import DemoTrainingResponse
from app.services.anomaly import train_demo_anomaly_model
from app.utils.auth import require_roles

router = APIRouter()


@router.post("/train-demo", response_model=DemoTrainingResponse)
def train_demo_anomaly_detector(
    current_user: dict = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
) -> DemoTrainingResponse:
    return DemoTrainingResponse.model_validate(train_demo_anomaly_model(force_retrain=True))
