import pandas as pd
from sklearn.ensemble import IsolationForest


class AnomalyDetectionService:
    """Small starter wrapper around Isolation Forest for later expansion."""

    def __init__(self) -> None:
        self.model = IsolationForest(contamination=0.1, random_state=42)

    def score(self, dataset: pd.DataFrame) -> list[float]:
        if dataset.empty:
            return []

        numeric_data = dataset.select_dtypes(include=["number"])
        if numeric_data.empty:
            return [0.0 for _ in range(len(dataset))]

        self.model.fit(numeric_data)
        scores = self.model.decision_function(numeric_data)
        return [float(score) for score in scores]
