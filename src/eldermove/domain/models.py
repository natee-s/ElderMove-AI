"""Stable data contracts between vision, analysis, and presentation layers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class HandSide(StrEnum):
    LEFT = "left"
    RIGHT = "right"
    UNKNOWN = "unknown"

    @classmethod
    def from_label(cls, value: str) -> "HandSide":
        return {"Left": cls.LEFT, "Right": cls.RIGHT}.get(value, cls.UNKNOWN)


class TaskMode(StrEnum):
    FREE_CHOICE = "free_choice"
    LEFT_GUIDED = "left_guided"
    RIGHT_GUIDED = "right_guided"

    @classmethod
    def from_label(cls, value: str) -> "TaskMode":
        return {
            "Free choice": cls.FREE_CHOICE,
            "Left guided": cls.LEFT_GUIDED,
            "Right guided": cls.RIGHT_GUIDED,
        }[value]


@dataclass(frozen=True)
class Point:
    x: float
    y: float
    visibility: float = 1.0


@dataclass(frozen=True)
class LandmarkObservation:
    time_seconds: float
    left_wrist: Point | None
    right_wrist: Point | None
    left_shoulder: Point | None
    right_shoulder: Point | None
    nose: Point | None
    left_hip: Point | None
    right_hip: Point | None
    pose_confidence: float
    target_marker: Point | None = None


@dataclass(frozen=True)
class AnalysisContext:
    task_name: str
    task_mode: TaskMode = TaskMode.FREE_CHOICE
    dominant_hand: HandSide = HandSide.UNKNOWN
    affected_hand: HandSide = HandSide.UNKNOWN
