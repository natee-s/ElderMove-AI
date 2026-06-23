"""Explainable movement features derived from normalized landmark time series."""

from __future__ import annotations

from collections.abc import Iterable
from math import hypot

import numpy as np

from src.eldermove.domain.models import LandmarkObservation, Point


def distance(first: Point, second: Point) -> float:
    return hypot(first.x - second.x, first.y - second.y)


def _torso_scale(item: LandmarkObservation) -> float | None:
    if item.left_shoulder and item.right_shoulder:
        return max(distance(item.left_shoulder, item.right_shoulder), 0.01)
    return None


def _hand_speeds(observations: list[LandmarkObservation], hand: str) -> list[tuple[float, float]]:
    values: list[tuple[float, float]] = []
    previous: LandmarkObservation | None = None
    for item in observations:
        wrist = getattr(item, f"{hand}_wrist")
        if previous is not None:
            prior_wrist = getattr(previous, f"{hand}_wrist")
            scale = _torso_scale(item)
            elapsed = item.time_seconds - previous.time_seconds
            if wrist and prior_wrist and scale and elapsed > 0:
                values.append((item.time_seconds, distance(wrist, prior_wrist) / scale / elapsed))
        previous = item
    return values


def _range_of_motion(observations: Iterable[LandmarkObservation], hand: str) -> float:
    distances: list[float] = []
    for item in observations:
        wrist = getattr(item, f"{hand}_wrist")
        shoulder = getattr(item, f"{hand}_shoulder")
        scale = _torso_scale(item)
        if wrist and shoulder and scale:
            distances.append(distance(wrist, shoulder) / scale)
    return max(distances, default=0.0) - min(distances, default=0.0)


def _smoothness_score(speeds: list[float]) -> float:
    if len(speeds) < 3:
        return 0.0
    jerk_proxy = float(np.mean(np.abs(np.diff(speeds))))
    return float(np.clip(100 * (1 - jerk_proxy / 2.0), 0, 100))


def _trunk_compensation(observations: list[LandmarkObservation]) -> float:
    normalized_drift: list[float] = []
    baseline: float | None = None
    for item in observations:
        if not (item.nose and item.left_hip and item.right_hip):
            continue
        midpoint = Point((item.left_hip.x + item.right_hip.x) / 2, (item.left_hip.y + item.right_hip.y) / 2)
        scale = _torso_scale(item)
        if not scale:
            continue
        offset = (item.nose.x - midpoint.x) / scale
        baseline = offset if baseline is None else baseline
        normalized_drift.append(abs(offset - baseline))
    return float(np.clip(np.percentile(normalized_drift, 90, method="nearest") * 100, 0, 100)) if normalized_drift else 0.0


def _accuracy(observations: list[LandmarkObservation], hand: str) -> tuple[float | None, float | None]:
    errors: list[float] = []
    for item in observations:
        wrist, target, scale = getattr(item, f"{hand}_wrist"), item.target_marker, _torso_scale(item)
        if wrist and target and scale:
            errors.append(distance(wrist, target) / scale)
    if not errors:
        return None, None
    endpoint_error = float(np.percentile(errors, 10, method="nearest"))
    return endpoint_error, float(np.clip(100 * (1 - endpoint_error / 1.5), 0, 100))


def calculate_metrics(observations: list[LandmarkObservation]) -> dict[str, float | list[dict[str, float]]]:
    """Return unitless, camera-normalized markers; never clinical diagnoses."""
    left_series = _hand_speeds(observations, "left")
    right_series = _hand_speeds(observations, "right")
    left_speeds = [value for _, value in left_series]
    right_speeds = [value for _, value in right_series]
    left_activity = float(np.sum(left_speeds))
    right_activity = float(np.sum(right_speeds))
    activity_total = left_activity + right_activity
    asymmetry = abs(left_activity - right_activity) / activity_total * 100 if activity_total else 0.0
    all_speeds = left_speeds + right_speeds

    time_axis = sorted({time for time, _ in left_series} | {time for time, _ in right_series})
    left_map, right_map = dict(left_series), dict(right_series)
    left_error, left_accuracy = _accuracy(observations, "left")
    right_error, right_accuracy = _accuracy(observations, "right")
    timeseries = [
        {"time_seconds": time, "left_speed": left_map.get(time, 0.0), "right_speed": right_map.get(time, 0.0)}
        for time in time_axis
    ]
    return {
        "mean_speed": float(np.mean(all_speeds)) if all_speeds else 0.0,
        "peak_speed": float(np.max(all_speeds)) if all_speeds else 0.0,
        "left_mean_speed": float(np.mean(left_speeds)) if left_speeds else 0.0,
        "right_mean_speed": float(np.mean(right_speeds)) if right_speeds else 0.0,
        "left_range_of_motion": _range_of_motion(observations, "left"),
        "right_range_of_motion": _range_of_motion(observations, "right"),
        "left_activity": left_activity,
        "right_activity": right_activity,
        "hand_use_asymmetry": asymmetry,
        "smoothness_score": _smoothness_score(all_speeds),
        "left_smoothness_score": _smoothness_score(left_speeds),
        "right_smoothness_score": _smoothness_score(right_speeds),
        "left_endpoint_error": left_error,
        "right_endpoint_error": right_error,
        "left_accuracy_score": left_accuracy,
        "right_accuracy_score": right_accuracy,
        "trunk_compensation_score": _trunk_compensation(observations),
        "timeseries": timeseries,
    }
