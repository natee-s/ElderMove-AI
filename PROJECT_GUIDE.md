# ElderMove AI - Team Guide

## Purpose

ElderMove AI is a local-first prototype for the E-Health Hackathon 2026. The supplied input is one video in which a participant can use either hand freely. The system measures observed hand use, Speed, Range of Motion, and movement Quality to support discussion of hand-use asymmetry and possible learned non-use. It is not a diagnostic device.

## What the UI does

1. Optional context: habitual dominant hand and affected/weaker side.
2. Upload one free-choice upper-limb activity video.
3. Confirm consent and press **Analyze video**.
4. Read a simple result: observed primary hand, use share, pose quality, left/right movement comparison, and an optional observation when a learned non-use pattern is strong enough to mention.

The app does not require left-guided or right-guided videos because they are not part of the supplied hackathon input.

## Interpretation model

`Observed primary hand` is the hand with the greater normalized wrist-motion activity in the video. It is not declared to be the participant's historical dominant hand.

When the user identifies an affected side, the app may display an observation only if the other side is used much more in the free-choice video. This is a prompt for professional review, not a conclusion that learned non-use exists.

## Technical pipeline

```text
Free-choice video
  -> OpenCV frame decoder, resize, 4 Hz sampler
  -> MediaPipe Holistic pose landmarks
  -> normalized wrist time series
  -> Speed, ROM, smoothness, trunk compensation, hand-use asymmetry
  -> transparent screening rules
  -> local Streamlit report and JSON export
```

## Why this stack

- **Streamlit** provides a practical local demo UI without a backend API.
- **MediaPipe Holistic** estimates upper-body landmarks on-device and avoids cloud transmission.
- **OpenCV** decodes video and reduces 1080p frames to 640 px before inference for predictable demo speed.
- **NumPy/Pandas** calculate reproducible metrics and create exportable data.
- **Pytest** validates scoring logic separately from the UI.

## Metrics

All distance features are normalized by shoulder width in the image to reduce camera-distance variation within a video.

| Metric | Meaning |
| --- | --- |
| Speed | Wrist displacement per second. |
| Range | Change in wrist-to-shoulder distance. |
| Quality | Smoothness score from speed changes; higher means more continuous movement. |
| Hand-use asymmetry | Difference in observed left/right activity. |
| Trunk compensation | Head-to-hip-midpoint drift during the activity. |

The code contains optional red-marker endpoint Accuracy and a three-task session scorer for future data collection, but neither is used in the current single-video UI. The UI deliberately does not show an Accuracy value when the supplied video has no target marker.

## Code map

| Path | Responsibility |
| --- | --- |
| `app/streamlit_app.py` | Single-video upload, result UI, export. |
| `src/eldermove/pipeline.py` | Video decoding, sampling, pose inference orchestration. |
| `src/eldermove/vision/mediapipe_detector.py` | MediaPipe adapter. |
| `src/eldermove/analysis/metrics.py` | Explainable movement calculations. |
| `src/eldermove/analysis/scoring.py` | Single-video hand-use and learned non-use observation rules. |
| `src/eldermove/session.py` | Future optional multi-task scorer, not used by the UI. |
| `tests/` | Automated formula and rule tests. |

## Run

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
.\.venv\Scripts\streamlit.exe run app/streamlit_app.py
```

## Limits and safety

- Results depend on camera angle, visibility, lighting, clothing, and task adherence.
- A single video cannot verify historical handedness or diagnose learned non-use.
- Thresholds are prototype rules, not validated clinical cut-offs.
- A clinically deployed version needs consented labelled data, repeatability/fairness testing, a clinician workflow, and appropriate ethics/regulatory review.
