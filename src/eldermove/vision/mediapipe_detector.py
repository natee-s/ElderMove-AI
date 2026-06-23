"""Adapter that confines MediaPipe-specific details to one module."""

from __future__ import annotations

from typing import Any

from src.eldermove.domain.models import LandmarkObservation, Point


class MediaPipeHolisticDetector:
    def __init__(self, min_detection_confidence: float) -> None:
        import mediapipe as mp

        self._mp = mp
        self._engine = mp.solutions.holistic.Holistic(
            static_image_mode=False,
            model_complexity=0,
            smooth_landmarks=True,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_detection_confidence,
        )

    def close(self) -> None:
        self._engine.close()

    @staticmethod
    def _point(landmarks: Any, index: int) -> Point | None:
        if not landmarks:
            return None
        value = landmarks.landmark[index]
        return Point(value.x, value.y, getattr(value, "visibility", 1.0))

    def detect(self, rgb_frame: Any, time_seconds: float) -> LandmarkObservation:
        result = self._engine.process(rgb_frame)
        pose = result.pose_landmarks
        landmark = self._mp.solutions.pose.PoseLandmark
        confidence_points = [
            self._point(pose, landmark.LEFT_SHOULDER),
            self._point(pose, landmark.RIGHT_SHOULDER),
            self._point(pose, landmark.LEFT_WRIST),
            self._point(pose, landmark.RIGHT_WRIST),
        ]
        confidence = sum(point.visibility for point in confidence_points if point) / max(len([point for point in confidence_points if point]), 1)
        return LandmarkObservation(
            time_seconds=time_seconds,
            left_wrist=self._point(pose, landmark.LEFT_WRIST),
            right_wrist=self._point(pose, landmark.RIGHT_WRIST),
            left_shoulder=self._point(pose, landmark.LEFT_SHOULDER),
            right_shoulder=self._point(pose, landmark.RIGHT_SHOULDER),
            nose=self._point(pose, landmark.NOSE),
            left_hip=self._point(pose, landmark.LEFT_HIP),
            right_hip=self._point(pose, landmark.RIGHT_HIP),
            pose_confidence=confidence if pose else 0.0,
        )
