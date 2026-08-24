import pytest

from app.ai.baseline import StatisticalZScoreEngine


def test_no_history_uses_current_value() -> None:
    engine = StatisticalZScoreEngine(
        threshold=3.0,
        min_history=3,
    )

    result = engine.infer(
        current_value=50.0,
        history=[],
    )

    assert result.predicted_value == 50.0
    assert result.anomaly_score is None
    assert result.is_anomaly is False
    assert result.model_name == "statistical-zscore"
    assert result.model_version == "1.0"


def test_insufficient_history_does_not_flag_anomaly() -> None:
    engine = StatisticalZScoreEngine(
        threshold=3.0,
        min_history=5,
    )

    result = engine.infer(
        current_value=100.0,
        history=[20.0, 21.0, 19.0],
    )

    assert result.predicted_value == pytest.approx(20.0)
    assert result.anomaly_score is None
    assert result.is_anomaly is False


def test_normal_value_is_not_anomaly() -> None:
    engine = StatisticalZScoreEngine(
        threshold=3.0,
        min_history=5,
    )

    history = [
        48.0,
        49.0,
        50.0,
        51.0,
        52.0,
    ]

    result = engine.infer(
        current_value=51.0,
        history=history,
    )

    assert result.predicted_value == pytest.approx(50.0)
    assert result.anomaly_score is not None
    assert result.anomaly_score < 3.0
    assert result.is_anomaly is False


def test_extreme_value_is_detected_as_anomaly() -> None:
    engine = StatisticalZScoreEngine(
        threshold=3.0,
        min_history=5,
    )

    history = [
        48.0,
        49.0,
        50.0,
        51.0,
        52.0,
    ]

    result = engine.infer(
        current_value=80.0,
        history=history,
    )

    assert result.predicted_value == pytest.approx(50.0)
    assert result.anomaly_score is not None
    assert result.anomaly_score >= 3.0
    assert result.is_anomaly is True


def test_zero_variance_equal_value_is_normal() -> None:
    engine = StatisticalZScoreEngine(
        threshold=3.0,
        min_history=5,
    )

    result = engine.infer(
        current_value=50.0,
        history=[50.0, 50.0, 50.0, 50.0, 50.0],
    )

    assert result.predicted_value == 50.0
    assert result.anomaly_score == 0.0
    assert result.is_anomaly is False


def test_zero_variance_changed_value_is_anomaly() -> None:
    engine = StatisticalZScoreEngine(
        threshold=3.0,
        min_history=5,
    )

    result = engine.infer(
        current_value=55.0,
        history=[50.0, 50.0, 50.0, 50.0, 50.0],
    )

    assert result.predicted_value == 50.0
    assert result.anomaly_score is not None
    assert result.anomaly_score > 3.0
    assert result.is_anomaly is True


def test_invalid_engine_configuration_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="threshold must be greater than 0",
    ):
        StatisticalZScoreEngine(
            threshold=0,
            min_history=5,
        )

    with pytest.raises(
        ValueError,
        match="min_history must be at least 2",
    ):
        StatisticalZScoreEngine(
            threshold=3.0,
            min_history=1,
        )