from src.eldermove.analysis.metrics import calculate_metrics
from src.eldermove.domain.models import LandmarkObservation, Point


def sample(time: float, left_x: float, right_x: float) -> LandmarkObservation:
    return LandmarkObservation(
        time_seconds=time,
        left_wrist=Point(left_x, 0.55),
        right_wrist=Point(right_x, 0.55),
        left_shoulder=Point(0.35, 0.35),
        right_shoulder=Point(0.65, 0.35),
        nose=Point(0.50, 0.15),
        left_hip=Point(0.40, 0.75),
        right_hip=Point(0.60, 0.75),
        pose_confidence=0.9,
    )


def test_metrics_detect_more_left_activity() -> None:
    result = calculate_metrics([sample(0, 0.2, 0.7), sample(1, 0.6, 0.72), sample(2, 0.25, 0.70)])
    assert result["left_activity"] > result["right_activity"]
    assert result["hand_use_asymmetry"] > 0
    assert result["left_range_of_motion"] > result["right_range_of_motion"]

