from datetime import datetime

from pydantic import BaseModel


class DemoTrainingResponse(BaseModel):
    model_name: str
    trained_on_events: int
    feature_labels: list[str]
    vectorized_feature_count: int
    trained_at: datetime
    message: str
