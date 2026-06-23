# ElderMove AI

Local-first video movement screening prototype for the E-Health Hackathon 2026.

It estimates upper-limb movement markers from a seated-video recording: hand-use balance, range of motion, speed, smoothness, trunk compensation, and a transparent screening flag. It is a demo and decision-support tool, **not a diagnosis or a substitute for a clinician**.

## Architecture

```
Video / webcam recording
        |
        v
Consent + metadata --> frame-quality gate --> MediaPipe Pose / Hands
                                                    |
                                                    v
       JSON/CSV export <-- report builder <-- motion features <-- landmark time series
                                                    |
                                                    v
                                            explainable screen result
```

Raw video remains in the browser temporary upload area. The application does not persist it. Exports contain only derived measurements and declared, non-identifying task metadata.

## Run in VSCode

1. Open this folder in VSCode.
2. Run `powershell -ExecutionPolicy Bypass -File scripts/setup.ps1` from the integrated terminal. This creates `.venv` and installs dependencies.
3. Select the `.venv` interpreter if VSCode does not select it automatically.
4. Run `streamlit run app/streamlit_app.py`.
5. Open the URL printed by Streamlit, then upload a short seated upper-limb video.

Use `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1` to run the formula tests and syntax check.

## Streamlit Community Cloud

This project requires Python 3.12 because the pinned MediaPipe wheel does not support newer Python runtimes. The repository includes `runtime.txt` for Streamlit Community Cloud. Select `app/streamlit_app.py` as the main file, then redeploy after pushing this file.

## Recording protocol for the demo

- Seat the participant facing the camera, with shoulders, torso, and both hands visible.
- Use a stable, well-lit camera position at chest height.
- Ask for the same short reach-and-return task with both hands.
- Keep recordings under 3 minutes. The prototype downscales frames and samples at 4 Hz by default for predictable demo speed. Use environment settings only after validating speed on the demo machine.

## Interpretation boundary

The output is an exploratory movement screen. Thresholds are deliberately configurable and are not clinical cut-offs. A low quality score can result from occlusion, camera angle, loose clothing, or poor lighting. Any medical concern must be reviewed by a qualified health professional.
