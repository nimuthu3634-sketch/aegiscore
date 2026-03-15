from pydantic import BaseModel


class DashboardMetric(BaseModel):
    label: str
    value: str
    change: str


class DashboardSummary(BaseModel):
    metrics: list[DashboardMetric]
    highlights: list[str]
