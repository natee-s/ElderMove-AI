"""Orchestrates video decoding, quality checks, vision inference, and reporting."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import cv2

from src.eldermove.analysis.metrics import calculate_metrics
from src.eldermove.analysis.scoring import screen
from src.eldermove.config import AppConfig
from src.eldermove.domain.models import AnalysisContext, LandmarkObservation
from src.eldermove.vision.mediapipe_detector import MediaPipeHolisticDetector

ProgressCallback = Callable[[int, int], None]


class VideoAnalyzer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def analyze(self, video_path: Path, context: AnalysisContext, progress: ProgressCallback | None = None) -> dict:
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            raise ValueError("Unsupported or unreadable video file.")
        fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration_seconds = frame_count / fps if fps else 0
        if duration_seconds > self.config.max_video_seconds:
            capture.release()
            raise ValueError(f"Video exceeds {self.config.max_video_seconds:.0f}-second demo limit.")
        stride = max(int(round(fps / self.config.sample_rate_hz)), 1)
        expected_samples = max(frame_count // stride, 1)
        observations: list[LandmarkObservation] = []
        sampled = 0
        frame_index = 0
        detector = MediaPipeHolisticDetector(self.config.min_pose_confidence)
        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                if frame_index % stride == 0:
                    height, width = frame.shape[:2]
                    if width > self.config.max_inference_width:
                        scale = self.config.max_inference_width / width
                        frame = cv2.resize(
                            frame,
                            (self.config.max_inference_width, int(height * scale)),
                            interpolation=cv2.INTER_AREA,
                        )
                    target = self._detect_red_target(frame)
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    observation = detector.detect(rgb, frame_index / fps)
                    observation = replace(observation, target_marker=target)
                    observations.append(observation)
                    sampled += 1
                    if progress:
                        progress(sampled, expected_samples)
                frame_index += 1
        finally:
            detector.close()
            capture.release()
        valid = [item for item in observations if item.pose_confidence >= self.config.min_pose_confidence]
        if len(valid) < self.config.min_valid_samples:
            raise ValueError("Too few usable pose samples. Re-record with the full upper body and both hands visible.")
        metrics = calculate_metrics(valid)
        coverage = len(valid) / max(len(observations), 1) * 100
        warnings: list[str] = []
        if coverage < 80:
            warnings.append("Some frames had low pose confidence. Treat measurements cautiously.")
        if metrics["left_activity"] == 0 or metrics["right_activity"] == 0:
            warnings.append("One hand was not tracked in enough frames; check camera framing before comparison.")
        if metrics["left_accuracy_score"] is None and metrics["right_accuracy_score"] is None:
            warnings.append("Red target marker was not detected; endpoint accuracy is unavailable.")
        screening = screen(metrics, coverage, context)
        timeseries = metrics.pop("timeseries")
        return {
            "report_version": "0.1.0",
            "context": {
                "task_name": context.task_name,
                "task_mode": context.task_mode.value,
                "dominant_hand": context.dominant_hand.value,
                "affected_hand": context.affected_hand.value,
            },
            "quality": {
                "sampled_frames": len(observations),
                "valid_pose_samples": len(valid),
                "pose_coverage_pct": coverage,
                "warnings": warnings,
                "target_marker_detected": metrics["left_accuracy_score"] is not None or metrics["right_accuracy_score"] is not None,
            },
            "metrics": metrics,
            "screening": screening,
            "timeseries": timeseries,
        }

    @staticmethod
    def _detect_red_target(frame: object) -> object:
        """Locate one large red circular target; returns normalized image coordinates."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, (0, 100, 80), (10, 255, 255)) | cv2.inRange(hsv, (170, 100, 80), (180, 255, 255))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(contour) < 120:
            return None
        moments = cv2.moments(contour)
        if not moments["m00"]:
            return None
        height, width = frame.shape[:2]
        from src.eldermove.domain.models import Point
        return Point(moments["m10"] / moments["m00"] / width, moments["m01"] / moments["m00"] / height)
