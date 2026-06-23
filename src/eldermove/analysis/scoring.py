"""Transparent rules for functional hand-use screening, not diagnosis."""

from __future__ import annotations

from src.eldermove.domain.models import AnalysisContext, HandSide, TaskMode


def _observed_hand(metrics: dict[str, float]) -> tuple[HandSide, float]:
    left, right = metrics["left_activity"], metrics["right_activity"]
    total = left + right
    if total == 0:
        return HandSide.UNKNOWN, 0.0
    leading = HandSide.LEFT if left >= right else HandSide.RIGHT
    return leading, max(left, right) / total * 100


def _hand_label(hand: HandSide) -> str:
    return {HandSide.LEFT: "มือซ้าย", HandSide.RIGHT: "มือขวา", HandSide.UNKNOWN: "ยังสรุปไม่ได้"}[hand]


def functional_use_summary(metrics: dict[str, float], context: AnalysisContext) -> dict[str, str | float]:
    observed, share = _observed_hand(metrics)
    if observed == HandSide.UNKNOWN:
        observed_text = "ยังอ่านการเคลื่อนไหวของมือได้ไม่เพียงพอ"
    elif share < 58:
        observed_text = "ใช้มือทั้งสองข้างใกล้เคียงกัน"
    else:
        observed_text = f"ระบบสังเกตว่าใช้{_hand_label(observed)}เด่นกว่า"

    if context.task_mode != TaskMode.FREE_CHOICE:
        comparison = "เป็น task ที่กำหนดข้างมือ จึงไม่ใช้ผลนี้เพื่อสรุปมือถนัด"
    elif context.dominant_hand == HandSide.UNKNOWN:
        comparison = "ยังไม่มีข้อมูลมือถนัดตามปกติสำหรับเปรียบเทียบ"
    elif observed == context.dominant_hand and share >= 58:
        comparison = "รูปแบบการใช้มือสอดคล้องกับมือถนัดที่รายงาน"
    elif observed == HandSide.UNKNOWN or share < 58:
        comparison = "การใช้มือยังใกล้เคียงกัน จึงยังสรุปความถนัดไม่ได้"
    else:
        comparison = "รูปแบบการใช้มือไม่สอดคล้องกับมือถนัดที่รายงาน"
    return {
        "observed_primary_hand": observed.value,
        "observed_use_share_pct": share,
        "observed_use_summary": observed_text,
        "preference_comparison": comparison,
    }


def learned_nonuse_signal(metrics: dict[str, float], context: AnalysisContext) -> tuple[str, str]:
    if context.task_mode != TaskMode.FREE_CHOICE:
        return "ยังไม่ประเมิน", "ให้ใช้คลิป task ใช้มืออิสระเท่านั้นในการคัดกรอง learned non-use"
    if context.affected_hand == HandSide.UNKNOWN:
        return "ข้อมูลไม่พอ", "ต้องระบุข้างที่อ่อนแรงหรือได้รับผลกระทบก่อน"
    observed, share = _observed_hand(metrics)
    if observed == HandSide.UNKNOWN or share < 58:
        return "ยังไม่ชัด", "การใช้มือทั้งสองข้างยังใกล้เคียงกัน"
    if observed != context.affected_hand and metrics["hand_use_asymmetry"] >= 35:
        return "มีสัญญาณให้ตรวจต่อ", "ใช้มือข้างที่ไม่อ่อนแรงเด่นกว่าใน task อิสระ ควรเปรียบเทียบผล task บังคับใช้ซ้ายและขวา"
    return "ไม่พบสัญญาณจากคลิปนี้", "คลิปเดียวไม่เพียงพอสำหรับยืนยันหรือปฏิเสธ learned non-use"


def screen(metrics: dict[str, float], pose_coverage_pct: float, context: AnalysisContext) -> dict[str, str | float]:
    if pose_coverage_pct < 60:
        return {
            "level": "บันทึกวิดีโอใหม่",
            "rationale": "เห็น pose น้อยกว่า 60% จึงยังไม่ควรแปลผล",
            "observed_primary_hand": HandSide.UNKNOWN.value,
            "observed_use_share_pct": 0.0,
            "observed_use_summary": "คุณภาพวิดีโอไม่พอ",
            "preference_comparison": "ปรับแสงและจัดให้เห็นลำตัวกับมือทั้งสองข้าง",
            "learned_nonuse_signal": "ยังไม่ประเมิน",
            "learned_nonuse_rationale": "ต้องมีวิดีโอที่อ่าน pose ได้ก่อน",
        }
    use = functional_use_summary(metrics, context)
    signal, signal_reason = learned_nonuse_signal(metrics, context)
    review_reasons: list[str] = []
    if context.task_mode == TaskMode.FREE_CHOICE and metrics["hand_use_asymmetry"] >= 55:
        review_reasons.append("ความต่างการใช้มือสูง")
    if metrics["trunk_compensation_score"] > 35:
        review_reasons.append("มีการชดเชยด้วยลำตัว")
    level = "ควรเปรียบเทียบ task เพิ่ม" if review_reasons else "พร้อมเปรียบเทียบกับคลิปอีกข้าง"
    return {
        "level": level,
        "rationale": "; ".join(review_reasons) if review_reasons else "ผลนี้ควรอ่านร่วมกับคลิป task บังคับใช้ซ้ายและขวา",
        **use,
        "learned_nonuse_signal": signal,
        "learned_nonuse_rationale": signal_reason,
    }
