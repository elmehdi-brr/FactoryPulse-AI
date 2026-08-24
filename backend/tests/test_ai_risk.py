import pytest

from app.ai.risk import AnomalyRiskEvaluator


def test_normal_prediction_does_not_alert() -> None:
    evaluator = AnomalyRiskEvaluator(
        high_threshold=5.0,
        critical_threshold=8.0,
    )

    result = evaluator.assess(
        is_anomaly=False,
        anomaly_score=10.0,
    )

    assert result.should_alert is False
    assert result.severity is None


def test_anomaly_without_score_is_medium() -> None:
    evaluator = AnomalyRiskEvaluator()

    result = evaluator.assess(
        is_anomaly=True,
        anomaly_score=None,
    )

    assert result.should_alert is True
    assert result.severity == "medium"


def test_medium_severity_anomaly() -> None:
    evaluator = AnomalyRiskEvaluator()

    result = evaluator.assess(
        is_anomaly=True,
        anomaly_score=4.0,
    )

    assert result.should_alert is True
    assert result.severity == "medium"


def test_high_severity_anomaly() -> None:
    evaluator = AnomalyRiskEvaluator()

    result = evaluator.assess(
        is_anomaly=True,
        anomaly_score=6.0,
    )

    assert result.should_alert is True
    assert result.severity == "high"


def test_critical_severity_anomaly() -> None:
    evaluator = AnomalyRiskEvaluator()

    result = evaluator.assess(
        is_anomaly=True,
        anomaly_score=9.0,
    )

    assert result.should_alert is True
    assert result.severity == "critical"


def test_invalid_risk_thresholds_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="high_threshold must be greater than 0",
    ):
        AnomalyRiskEvaluator(
            high_threshold=0,
            critical_threshold=8.0,
        )

    with pytest.raises(
        ValueError,
        match="critical_threshold must be greater than high_threshold",
    ):
        AnomalyRiskEvaluator(
            high_threshold=5.0,
            critical_threshold=5.0,
        )