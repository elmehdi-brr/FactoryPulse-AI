from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True, slots=True)
class InferenceResult:
    predicted_value: float
    anomaly_score: float | None
    is_anomaly: bool
    model_name: str
    model_version: str


class InferenceEngine(Protocol):
    model_name: str
    model_version: str

    def infer(
        self,
        current_value: float,
        history: Sequence[float],
    ) -> InferenceResult:
        ...