from src.eldermove.analysis.scoring import screen
from src.eldermove.domain.models import AnalysisContext, HandSide, TaskMode


def test_low_quality_requires_repeat() -> None:
    result = screen(
        {"left_activity": 1.0, "right_activity": 1.0, "hand_use_asymmetry": 0.0, "smoothness_score": 90.0, "trunk_compensation_score": 0.0},
        45.0,
        AnalysisContext("reach"),
    )
    assert result["level"] == "บันทึกวิดีโอใหม่"


def test_asymmetry_requests_review() -> None:
    result = screen(
        {"left_activity": 5.0, "right_activity": 1.0, "hand_use_asymmetry": 70.0, "smoothness_score": 85.0, "trunk_compensation_score": 5.0},
        95.0,
        AnalysisContext("reach", task_mode=TaskMode.FREE_CHOICE, affected_hand=HandSide.RIGHT),
    )
    assert result["level"] == "ควรเปรียบเทียบ task เพิ่ม"
    assert result["learned_nonuse_signal"] == "มีสัญญาณให้ตรวจต่อ"
