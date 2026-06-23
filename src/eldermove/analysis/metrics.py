"""Explainable movement features derived from normalized landmark time series."""

from __future__ import annotations

from collections.abc import Iterable
from math import acos, degrees, hypot

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


def _path_efficiency(observations: list[LandmarkObservation], hand: str) -> float:
    points = [getattr(item, f"{hand}_wrist") for item in observations]
    points = [point for point in points if point]
    if len(points) < 3:
        return 0.0
    path = sum(distance(first, second) for first, second in zip(points, points[1:]))
    return float(np.clip(distance(points[0], points[-1]) / max(path, 0.001) * 100, 0, 100))


def _trajectory_control(speeds: list[float]) -> float:
    if len(speeds) < 3 or np.mean(speeds) <= 0:
        return 0.0
    variation = float(np.std(speeds) / max(np.mean(speeds), 0.001))
    return float(np.clip(100 * (1 - variation / 2.5), 0, 100))


def _hesitation_count(speeds: list[float]) -> int:
    if len(speeds) < 4 or max(speeds) <= 0:
        return 0
    threshold = max(speeds) * 0.18
    low = [speed < threshold for speed in speeds]
    return sum(1 for was_low, is_low in zip(low, low[1:]) if not was_low and is_low)


def _elbow_range(observations: list[LandmarkObservation], hand: str) -> float:
    angles: list[float] = []
    for item in observations:
        shoulder, elbow, wrist = getattr(item, f"{hand}_shoulder"), getattr(item, f"{hand}_elbow"), getattr(item, f"{hand}_wrist")
        if not (shoulder and elbow and wrist):
            continue
        first = (shoulder.x - elbow.x, shoulder.y - elbow.y)
        second = (wrist.x - elbow.x, wrist.y - elbow.y)
        denominator = hypot(*first) * hypot(*second)
        if denominator:
            cosine = np.clip((first[0] * second[0] + first[1] * second[1]) / denominator, -1, 1)
            angles.append(degrees(acos(cosine)))
    return max(angles, default=0.0) - min(angles, default=0.0)


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
        "left_path_efficiency": _path_efficiency(observations, "left"),
        "right_path_efficiency": _path_efficiency(observations, "right"),
        "left_trajectory_control": _trajectory_control(left_speeds),
        "right_trajectory_control": _trajectory_control(right_speeds),
        "left_hesitation_count": _hesitation_count(left_speeds),
        "right_hesitation_count": _hesitation_count(right_speeds),
        "left_elbow_range": _elbow_range(observations, "left"),
        "right_elbow_range": _elbow_range(observations, "right"),
        "trunk_compensation_score": _trunk_compensation(observations),
        "timeseries": timeseries,
    }
