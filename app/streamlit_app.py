"""Single-video free-choice assessment interface for the hackathon prototype."""
from __future__ import annotations
import sys
import tempfile
from pathlib import Path
import pandas as pd
import streamlit as st
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from src.eldermove.config import AppConfig
from src.eldermove.domain.models import AnalysisContext, HandSide, TaskMode
from src.eldermove.pipeline import VideoAnalyzer
from src.eldermove.reporting import report_as_json
st.set_page_config(page_title="ElderMove AI", page_icon="EM", layout="wide")

def hand_name(value): return {"left":"มือซ้าย","right":"มือขวา","unknown":"ยังสรุปไม่ได้"}.get(value,value)
def analyze(uploaded, context):
    with tempfile.NamedTemporaryFile(suffix=Path(uploaded.name).suffix or ".mp4",delete=False) as f:
        f.write(uploaded.getbuffer()); path=Path(f.name)
    try:
        bar=st.progress(0,text="กำลังเตรียมวิดีโอ")
        return VideoAnalyzer(AppConfig.from_environment()).analyze(path,context,lambda c,t:bar.progress(int(c/max(t,1)*100),text=f"กำลังวิเคราะห์ {c}/{t} frames"))
    except Exception as error: st.error(f"วิเคราะห์ไม่สำเร็จ: {error}"); return None
    finally: path.unlink(missing_ok=True)
def show_results(report):
    m,s,q=report["metrics"],report["screening"],report["quality"]
    st.divider(); st.header("ผลวิเคราะห์จากคลิปนี้")
    a,b,c=st.columns(3); a.metric("มือที่ระบบสังเกตว่าใช้เด่น",hand_name(s["observed_primary_hand"])); b.metric("สัดส่วนการใช้มือที่เด่น",f"{s['observed_use_share_pct']:.0f}%"); c.metric("คุณภาพการอ่านท่าทาง",f"{q['pose_coverage_pct']:.0f}%")
    st.info(s["observed_use_summary"]); st.caption(s["preference_comparison"])
    st.subheader("เปรียบเทียบการเคลื่อนไหวของมือ")
    st.dataframe(pd.DataFrame([{"มือ":"ซ้าย","Speed":m["left_mean_speed"],"Range":m["left_range_of_motion"],"Quality":m["left_smoothness_score"]},{"มือ":"ขวา","Speed":m["right_mean_speed"],"Range":m["right_range_of_motion"],"Quality":m["right_smoothness_score"]}]).style.format({"Speed":"{:.2f}","Range":"{:.2f}","Quality":"{:.0f}"}),use_container_width=True,hide_index=True)
    st.caption("Speed และ Range ถูก normalize ตามความกว้างไหล่ในภาพ ส่วน Quality คือความต่อเนื่องของการเคลื่อนไหว")
    if s["learned_nonuse_signal"] == "มีสัญญาณให้ตรวจต่อ":
        st.subheader("ข้อสังเกตจากรูปแบบการใช้มือ")
        st.write("พบความต่างการเลือกใช้มือที่ควรให้ผู้เชี่ยวชาญพิจารณาร่วมกับข้อมูลทางคลินิก")
        st.caption(s["learned_nonuse_rationale"])
    elif report["context"]["affected_hand"] != "unknown":
        st.caption("จากคลิปนี้ยังไม่มีรูปแบบการใช้มือที่ชัดพอจะตั้งข้อสังเกตเรื่อง learned non-use")
    if not q["target_marker_detected"]: st.warning("คลิปโจทย์ไม่มี target marker จึงไม่สรุป endpoint Accuracy เพื่อไม่สร้างค่าที่ไม่มีหลักฐาน")
    with st.expander("ดูกราฟความเร็วและข้อมูลทางเทคนิค"):
        frame=pd.DataFrame(report["timeseries"])
        if not frame.empty: st.line_chart(frame.set_index("time_seconds")[["left_speed","right_speed"]])
    st.download_button("ดาวน์โหลดรายงาน JSON",report_as_json(report),"eldermove_report.json","application/json")
def main():
    st.title("ElderMove AI"); st.caption("วิเคราะห์การใช้มืออิสระจากวิดีโอ 1 คลิป ด้วย AI pose estimation บนเครื่อง")
    st.info("ถ่ายให้เห็นลำตัว ไหล่ และมือทั้งสองข้างตลอดคลิป แล้วให้ผู้เข้าร่วมทำกิจกรรมตามธรรมชาติ")
    a,b=st.columns(2)
    with a: dominant=st.selectbox("มือที่ถนัดตามปกติ (ถ้าทราบ)",["Unknown","Left","Right"])
    with b: affected=st.selectbox("มือข้างที่อ่อนแรงหรือได้รับผลกระทบ (ถ้าทราบ)",["Unknown","Left","Right"])
    uploaded=st.file_uploader("อัปโหลดคลิปการใช้มืออิสระ",type=["mp4","mov","avi"]); consent=st.checkbox("ยืนยันว่าได้รับความยินยอมในการประมวลผลวิดีโอสำหรับเดโมแล้ว")
    if uploaded: st.video(uploaded)
    if st.button("วิเคราะห์คลิป",type="primary",use_container_width=True,disabled=not(uploaded and consent)):
        report=analyze(uploaded,AnalysisContext("Free-choice upper-limb activity",TaskMode.FREE_CHOICE,HandSide.from_label(dominant),HandSide.from_label(affected)))
        if report: st.session_state["report"]=report
    if report:=st.session_state.get("report"): show_results(report)
if __name__=="__main__": main()
