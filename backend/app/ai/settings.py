from dataclasses import dataclass

from app.ai.base import InferenceEngine
from app.ai.baseline import StatisticalZScoreEngine
from app.ai.risk import AnomalyRiskEvaluator


@dataclass(frozen=True, slots=True)
class AISettings:
    is_enabled: bool = True

    engine_name: str = "statistical-zscore"

    anomaly_threshold: float = 3.0

    min_history: int = 10

    history_limit: int = 50

    high_risk_threshold: float = 5.0

    critical_risk_threshold: float = 8.0


DEFAULT_AI_SETTINGS = AISettings()


def build_inference_engine(
    settings: AISettings,
) -> InferenceEngine:
    if settings.engine_name == "statistical-zscore":
        return StatisticalZScoreEngine(
            threshold=settings.anomaly_threshold,
            min_history=settings.min_history,
        )

    raise ValueError(
        f"Unsupported inference engine: {settings.engine_name}"
    )


def build_risk_evaluator(
    settings: AISettings,
) -> AnomalyRiskEvaluator:
    return AnomalyRiskEvaluator(
        high_threshold=settings.high_risk_threshold,
        critical_threshold=settings.critical_risk_threshold,
    )