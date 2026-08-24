from math import isclose
from statistics import fmean, pstdev
from typing import Sequence

from app.ai.base import InferenceResult


class StatisticalZScoreEngine:
    model_name = "statistical-zscore"
    model_version = "1.0"

    def __init__(
        self,
        threshold: float = 3.0,
        min_history: int = 10,
    ) -> None:
        if threshold <= 0:
            raise ValueError("threshold must be greater than 0")

        if min_history < 2:
            raise ValueError("min_history must be at least 2")

        self.threshold = threshold
        self.min_history = min_history

    def infer(
        self,
        current_value: float,
        history: Sequence[float],
    ) -> InferenceResult:
        values = [float(value) for value in history]
        current_value = float(current_value)

        if not values:
            return InferenceResult(
                predicted_value=current_value,
                anomaly_score=None,
                is_anomaly=False,
                model_name=self.model_name,
                model_version=self.model_version,
            )

        expected_value = fmean(values)

        if len(values) < self.min_history:
            return InferenceResult(
                predicted_value=expected_value,
                anomaly_score=None,
                is_anomaly=False,
                model_name=self.model_name,
                model_version=self.model_version,
            )

        standard_deviation = pstdev(values)

        if isclose(standard_deviation, 0.0):
            anomaly_score = (
                0.0
                if isclose(current_value, expected_value)
                else self.threshold + 1.0
            )
        else:
            anomaly_score = abs(
                current_value - expected_value
            ) / standard_deviation

        return InferenceResult(
            predicted_value=expected_value,
            anomaly_score=anomaly_score,
            is_anomaly=anomaly_score >= self.threshold,
            model_name=self.model_name,
            model_version=self.model_version,
        )