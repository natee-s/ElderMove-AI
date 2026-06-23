"""Transparent clinical reasoning scorecard for the Virtual Rehab Vibe Coach."""

from __future__ import annotations

import numpy as np


def _relative(left: float, right: float) -> tuple[float, float]:
    maximum = max(left, right, 0.001)
    return left / maximum * 100, right / maximum * 100


def infer_hand_use(metrics: dict[str, float | None]) -> dict:
    """Infer functional dominance and possible learned non-use from explainable biomarkers."""
    left_speed, right_speed = _relative(float(metrics["left_mean_speed"]), float(metrics["right_mean_speed"]))
    left_control = (float(metrics["left_trajectory_control"]) + float(metrics["left_path_efficiency"])) / 2
    right_control = (float(metrics["right_trajectory_control"]) + float(metrics["right_path_efficiency"])) / 2
    left_quality = (float(metrics["left_smoothness_score"]) + left_control) / 2
    right_quality = (float(metrics["right_smoothness_score"]) + right_control) / 2
    left_score = .40 * left_speed + .30 * left_control + .30 * left_quality
    right_score = .40 * right_speed + .30 * right_control + .30 * right_quality
    predicted = "left" if left_score >= right_score else "right"
    gap = abs(left_score - right_score)
    confidence = "high" if gap >= 22 else "medium" if gap >= 10 else "low"
    left_activity, right_activity = float(metrics["left_activity"]), float(metrics["right_activity"])
    total_activity = left_activity + right_activity
    observed = "unknown" if total_activity == 0 else ("left" if left_activity >= right_activity else "right")
    observed_share = max(left_activity, right_activity) / max(total_activity, .001) * 100
    hypothesis = "uncertain"
    if confidence != "low" and observed != "unknown" and observed != predicted and observed_share >= 65:
        hypothesis = f"possible_{predicted}_learned_non_use"
    elif confidence != "low" and observed == predicted:
        hypothesis = "use_matches_prediction"
    return {
        "predicted_natural_dominance": predicted,
        "dominance_confidence": confidence,
        "dominance_score_gap": gap,
        "observed_hand_choice": observed,
        "observed_hand_share_pct": observed_share,
        "learned_non_use_hypothesis": hypothesis,
        "left_evidence_score": left_score,
        "right_evidence_score": right_score,
        "left_profile": {"speed": left_speed, "control": left_control, "quality": left_quality},
        "right_profile": {"speed": right_speed, "control": right_control, "quality": right_quality},
    }
