# Virtual Rehab Vibe Coach

## Purpose

Virtual Rehab Vibe Coach turns a free-choice upper-limb video into digital biomarkers and an explainable AI-assisted hypothesis about natural hand dominance, observed hand choice, and possible learned non-use. It is a hackathon prototype, not a diagnostic device.

## Sequential workflow

```text
MP4 video
-> AI Vision Core: OpenCV + MediaPipe landmarks
-> Metrics Engine: Speed, trajectory control, quality, hesitation, elbow range
-> Reasoning Scorecard: dominance and learned non-use hypothesis
-> Privacy-first Coach Agent: empathetic Thai feedback
-> Accessible Streamlit report
```

## Modules

### 1. AI Vision Core

`OpenCV` samples and resizes video frames. `MediaPipe Holistic` extracts shoulders, elbows, wrists, hips, and nose. Raw video remains temporary and is deleted after processing.

### 2. Digital Biomarkers

- **Speed**: normalized mean wrist velocity.
- **Trajectory control**: wrist velocity stability and path efficiency.
- **Quality**: combination of smoothness and trajectory control.
- **Hesitation**: count of meaningful speed drops during active movement.
- **Elbow range**: change in elbow flexion angle.
- **Compensation**: trunk motion relative to shoulder width.

All distances are normalized by shoulder width to reduce camera-distance bias.

### 3. Explainable Reasoning

For each side, the evidence score is:

```text
0.40 * relative Speed
+ 0.30 * trajectory control
+ 0.30 * movement Quality
```

The higher score is the estimated functional natural-dominance signal. The system separately measures current observed hand choice from motion activity. A possible learned non-use hypothesis appears only when a confident dominance signal conflicts with a strongly observed choice.

### 4. Agentic Coach and privacy

`VirtualRehabCoach` orchestrates the scorecard, validates confidence, and creates a supportive explanation. It receives only numeric biomarkers. No raw video, name, location, or identifier is sent to an external service. The current coach is deterministic so the deployed demo works without API keys; an LLM can later replace only the phrasing layer while preserving the scorecard as the source of truth.

## Output contract

```text
predicted_natural_dominance: left | right
dominance_confidence: high | medium | low
observed_hand_choice: left | right | unknown
learned_non_use_hypothesis: possible_<side>_learned_non_use | use_matches_prediction | uncertain
coach_message: Thai user-facing explanation
```

## Limits

- A single video cannot prove historical handedness or diagnose learned non-use.
- Low confidence is a valid output and should trigger repeat recording, not a stronger claim.
- Clinical deployment needs validation against clinician labels, representative data, repeatability testing, and ethics/regulatory review.

## Run

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
.\.venv\Scripts\streamlit.exe run app/streamlit_app.py
```
