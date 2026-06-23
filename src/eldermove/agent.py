"""Privacy-first orchestration and empathetic feedback without sending raw video to an LLM."""

from __future__ import annotations

from src.eldermove.analysis.reasoning import infer_hand_use


class VirtualRehabCoach:
    def run(self, report: dict) -> dict:
        metrics = report["metrics"]
        inference = infer_hand_use(metrics)
        confidence = inference["dominance_confidence"]
        predicted = "มือซ้าย" if inference["predicted_natural_dominance"] == "left" else "มือขวา"
        observed = "มือซ้าย" if inference["observed_hand_choice"] == "left" else "มือขวา"
        if confidence == "low":
            message = "รูปแบบการเคลื่อนไหวของสองข้างใกล้เคียงกัน ระบบยังไม่มั่นใจพอที่จะสรุปข้างที่เด่นจากคลิปนี้"
        elif inference["learned_non_use_hypothesis"].startswith("possible"):
            message = f"ระบบประเมินว่า {predicted} มีลักษณะการเคลื่อนไหวเด่นกว่า แต่ในคลิปเลือกใช้ {observed} เป็นหลัก ควรให้ผู้เชี่ยวชาญพิจารณาร่วมกับข้อมูลการฟื้นฟู"
        else:
            message = f"รูปแบบการใช้ {observed} ในคลิปสอดคล้องกับแขนที่ระบบประเมินว่าเด่นกว่า"
        return {"agent_name": "Virtual Rehab Vibe Coach", "privacy": "Only de-identified numeric biomarkers were used.", "inference": inference, "coach_message": message}
