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
st.markdown("""
<style>
:root { --ink:#123746; --muted:#66828c; --teal:#007b78; --teal-dark:#075b63; --aqua:#dff4f2; --surface:#ffffff; --line:#d8e7e9; }
.stApp { background:#f4f8f9; color:var(--ink); }
[data-testid="stHeader"] { background:rgba(244,248,249,.94); }
.block-container { max-width:1180px; padding-top:2.25rem; padding-bottom:3.5rem; }
h1,h2,h3 { color:var(--ink) !important; letter-spacing:0 !important; }
h1 { font-size:2.25rem !important; }
h2 { font-size:1.42rem !important; margin-top:2.2rem !important; }
.eyebrow { color:#087b79; font-size:.78rem; font-weight:700; text-transform:uppercase; letter-spacing:.08rem; margin:0 0 .35rem; }
.hero { background:#0e4552; color:white; padding:2.1rem 2.25rem; border-radius:8px; margin:0 0 2rem; }
.hero h1 { color:white !important; margin:0 !important; }
.hero p { color:#d4ecec; margin:.65rem 0 0; max-width:680px; font-size:1rem; }
div[data-testid="stFileUploader"] { background:var(--surface); border:1.5px dashed #78bdbb; border-radius:8px; padding:.85rem; }
div[data-testid="stFileUploader"] section { border:0 !important; background:#f7fcfc; }
div[data-testid="stSelectbox"] > div > div { background:white; border-color:var(--line); border-radius:6px; }
div[data-testid="stCheckbox"] { background:#eef8f7; border-left:3px solid var(--teal); padding:.75rem .9rem; border-radius:4px; }
button[kind="primary"] { background:var(--teal) !important; border:1px solid var(--teal) !important; border-radius:6px !important; font-weight:650 !important; min-height:2.8rem; }
button[kind="primary"]:hover { background:var(--teal-dark) !important; border-color:var(--teal-dark) !important; }
div[data-testid="stMetric"] { background:white; border:1px solid var(--line); border-top:4px solid #22a6a2; border-radius:8px; padding:1rem 1.1rem; min-height:120px; }
div[data-testid="stMetricLabel"] { color:var(--muted); font-size:.88rem; }
div[data-testid="stMetricValue"] { color:var(--ink); font-size:1.45rem; }
div[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:8px; overflow:hidden; }
div[data-testid="stAlert"] { border-radius:6px; }
details { background:white; border:1px solid var(--line); border-radius:6px; padding:.2rem .65rem; }
.section-kicker { color:#087b79; font-size:.8rem; font-weight:700; letter-spacing:.06rem; text-transform:uppercase; margin-top:1.8rem; }
</style>
""", unsafe_allow_html=True)

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
    st.markdown("<p class='section-kicker'>Assessment summary</p>", unsafe_allow_html=True); st.header("ผลวิเคราะห์จากคลิปนี้")
    a,b,c=st.columns(3); a.metric("มือที่ระบบสังเกตว่าใช้เด่น",hand_name(s["observed_primary_hand"])); b.metric("สัดส่วนการใช้มือที่เด่น",f"{s['observed_use_share_pct']:.0f}%"); c.metric("คุณภาพการอ่านท่าทาง",f"{q['pose_coverage_pct']:.0f}%")
    st.info(s["observed_use_summary"]); st.caption(s["preference_comparison"])
    st.markdown("<p class='section-kicker'>Movement comparison</p>", unsafe_allow_html=True); st.subheader("เปรียบเทียบการเคลื่อนไหวของมือ")
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
    st.markdown("""<section class='hero'><p class='eyebrow' style='color:#91d8d5'>Local movement assessment</p><h1>ElderMove AI</h1><p>วิเคราะห์รูปแบบการใช้มือจากวิดีโอ เพื่อช่วยให้เห็นความแตกต่างของการเคลื่อนไหวซ้ายและขวาอย่างเป็นระบบ</p></section>""", unsafe_allow_html=True)
    st.markdown("<p class='section-kicker'>New assessment</p>", unsafe_allow_html=True)
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
