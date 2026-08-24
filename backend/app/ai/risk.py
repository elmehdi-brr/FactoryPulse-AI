from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    should_alert: bool
    severity: str | None


class AnomalyRiskEvaluator:
    def __init__(
        self,
        high_threshold: float = 5.0,
        critical_threshold: float = 8.0,
    ) -> None:
        if high_threshold <= 0:
            raise ValueError(
                "high_threshold must be greater than 0"
            )

        if critical_threshold <= high_threshold:
            raise ValueError(
                "critical_threshold must be greater than high_threshold"
            )

        self.high_threshold = high_threshold
        self.critical_threshold = critical_threshold

    def assess(
        self,
        is_anomaly: bool,
        anomaly_score: float | None,
    ) -> RiskAssessment:
        if not is_anomaly:
            return RiskAssessment(
                should_alert=False,
                severity=None,
            )

        if anomaly_score is None:
            return RiskAssessment(
                should_alert=True,
                severity="medium",
            )

        if anomaly_score >= self.critical_threshold:
            severity = "critical"
        elif anomaly_score >= self.high_threshold:
            severity = "high"
        else:
            severity = "medium"

        return RiskAssessment(
            should_alert=True,
            severity=severity,
        )