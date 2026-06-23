"""Application configuration kept outside UI and analysis logic."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppConfig:
    sample_rate_hz: float = 4.0
    min_pose_confidence: float = 0.55
    max_video_seconds: float = 180.0
    max_inference_width: int = 640
    min_valid_samples: int = 12

    @classmethod
    def from_environment(cls) -> "AppConfig":
        return cls(
            sample_rate_hz=float(os.getenv("ELDERMOVE_SAMPLE_RATE_HZ", "4")),
            min_pose_confidence=float(os.getenv("ELDERMOVE_MIN_POSE_CONFIDENCE", "0.55")),
            max_video_seconds=float(os.getenv("ELDERMOVE_MAX_VIDEO_SECONDS", "180")),
            max_inference_width=int(os.getenv("ELDERMOVE_MAX_INFERENCE_WIDTH", "640")),
        )
