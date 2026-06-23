"""Privacy-first orchestration and empathetic feedback without sending raw video to an LLM."""

from __future__ import annotations

from src.eldermove.analysis.reasoning import infer_hand_use


def _camera_label(anatomical_side: str) -> str:
    """Map MediaPipe anatomical side to the screen-side labels used in supplied clips."""
    return {"left": "right", "right": "left"}.get(anatomical_side, anatomical_side)


class VirtualRehabCoach:
    def run(self, report: dict) -> dict:
        metrics = report["metrics"]
        inference = infer_hand_use(metrics)
        presentation = {
            "predicted_natural_dominance": _camera_label(inference["predicted_natural_dominance"]),
            "observed_hand_choice": _camera_label(inference["observed_hand_choice"]),
        }
        hypothesis = inference["learned_non_use_hypothesis"]
        if hypothesis.startswith("possible_"):
            side = hypothesis.split("_")[1]
            presentation["learned_non_use_hypothesis"] = f"possible_{_camera_label(side)}_learned_non_use"
        else:
            presentation["learned_non_use_hypothesis"] = hypothesis
        confidence = inference["dominance_confidence"]
        predicted = "มือซ้าย" if presentation["predicted_natural_dominance"] == "left" else "มือขวา"
        observed = "มือซ้าย" if presentation["observed_hand_choice"] == "left" else "มือขวา"
        if confidence == "low":
            message = "รูปแบบการเคลื่อนไหวของสองข้างใกล้เคียงกัน ระบบยังไม่มั่นใจพอที่จะสรุปข้างที่เด่นจากคลิปนี้"
        elif inference["learned_non_use_hypothesis"].startswith("possible"):
            message = f"ระบบประเมินว่า {predicted} มีลักษณะการเคลื่อนไหวเด่นกว่า แต่ในคลิปเลือกใช้ {observed} เป็นหลัก ควรให้ผู้เชี่ยวชาญพิจารณาร่วมกับข้อมูลการฟื้นฟู"
        else:
            message = f"รูปแบบการใช้ {observed} ในคลิปสอดคล้องกับแขนที่ระบบประเมินว่าเด่นกว่า"
        return {"agent_name": "Virtual Rehab Vibe Coach", "privacy": "Only de-identified numeric biomarkers were used.", "inference": inference, "presentation": presentation, "coach_message": message}
