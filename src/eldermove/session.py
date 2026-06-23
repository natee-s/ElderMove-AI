"""Combines the three standardized tasks into one explainable session result."""

from __future__ import annotations

from src.eldermove.domain.models import HandSide


def _pair_score(left: float, right: float) -> tuple[float, float]:
    maximum = max(left, right, 0.001)
    return left / maximum * 100, right / maximum * 100


def build_session_report(reports: dict[str, dict]) -> dict:
    free, left_task, right_task = reports["free_choice"], reports["left_guided"], reports["right_guided"]
    left = left_task["metrics"]
    right = right_task["metrics"]
    speed_l, speed_r = _pair_score(left["left_mean_speed"], right["right_mean_speed"])
    quality_l, quality_r = left["left_smoothness_score"], right["right_smoothness_score"]
    accuracy_l, accuracy_r = left["left_accuracy_score"], right["right_accuracy_score"]
    has_accuracy = accuracy_l is not None and accuracy_r is not None
    if has_accuracy:
        score_l = .35 * speed_l + .40 * accuracy_l + .25 * quality_l
        score_r = .35 * speed_r + .40 * accuracy_r + .25 * quality_r
    else:
        score_l, score_r = .60 * speed_l + .40 * quality_l, .60 * speed_r + .40 * quality_r
    preferred = HandSide.LEFT if score_l > score_r else HandSide.RIGHT
    confidence = abs(score_l - score_r)
    functional = "ใกล้เคียงกัน" if confidence < 10 else f"{preferred.value}"
    observed = free["screening"]["observed_primary_hand"]
    affected = free["context"]["affected_hand"]
    possible_nonuse = (
        affected in {"left", "right"} and observed in {"left", "right"} and observed != affected
        and (score_l if affected == "left" else score_r) >= 60
    )
    return {
        "functional_preference_estimate": functional,
        "estimate_confidence_gap": confidence,
        "free_choice_observed_hand": observed,
        "habitual_hand_reported": free["context"]["dominant_hand"],
        "possible_learned_nonuse": "มีสัญญาณให้ตรวจต่อ" if possible_nonuse else "ยังไม่พบจาก session นี้",
        "accuracy_available": has_accuracy,
        "hand_performance": {
            "left": {"speed_score": speed_l, "accuracy_score": accuracy_l, "quality_score": quality_l, "functional_score": score_l},
            "right": {"speed_score": speed_r, "accuracy_score": accuracy_r, "quality_score": quality_r, "functional_score": score_r},
        },
    }
