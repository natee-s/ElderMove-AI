"""Virtual Rehab Vibe Coach - accessible local Streamlit interface."""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
import pandas as pd
import streamlit as st
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.eldermove.config import AppConfig
from src.eldermove.domain.models import AnalysisContext, HandSide, TaskMode
from src.eldermove.pipeline import VideoAnalyzer
from src.eldermove.reporting import report_as_json

st.set_page_config(page_title="Virtual Rehab Vibe Coach",page_icon="VR",layout="wide")
st.markdown("""<style>
.stApp{background:#f4f8f8;color:#163b46}.block-container{max-width:1180px;padding-top:2rem}.hero{background:#104b57;border-radius:8px;padding:2rem 2.2rem;color:#fff}.hero h1{color:#fff;margin:0;font-size:2.25rem}.hero p{color:#d7eeee;margin:.55rem 0 0;font-size:1rem}.eyebrow{color:#9de0d9;font-size:.76rem;font-weight:700;letter-spacing:.08rem;text-transform:uppercase}h2,h3{color:#163b46!important}div[data-testid="stMetric"]{background:#fff;border:1px solid #d6e7e7;border-top:4px solid #0d9992;border-radius:8px;padding:1rem}button[kind="primary"]{background:#087b78!important;border-color:#087b78!important;border-radius:6px!important;min-height:2.8rem;font-weight:700}div[data-testid="stFileUploader"]{background:#fff;border:1.5px dashed #74bbb7;border-radius:8px;padding:.8rem}div[data-testid="stAlert"]{border-radius:6px}details{background:#fff;border:1px solid #d6e7e7;border-radius:6px;padding:.3rem .65rem}</style>""",unsafe_allow_html=True)

def label(side): return {"left":"มือซ้าย","right":"มือขวา","unknown":"ยังสรุปไม่ได้"}.get(side,side)
def analyze(uploaded):
    with tempfile.NamedTemporaryFile(suffix=Path(uploaded.name).suffix or '.mp4',delete=False) as f: f.write(uploaded.getbuffer()); path=Path(f.name)
    try:
        p=st.progress(0,text="AI Vision กำลังสกัดข้อมูลการเคลื่อนไหว")
        return VideoAnalyzer(AppConfig.from_environment()).analyze(path,AnalysisContext("Free-choice activity",TaskMode.FREE_CHOICE,HandSide.UNKNOWN,HandSide.UNKNOWN),lambda c,t:p.progress(int(c/max(t,1)*100),text=f"กำลังวิเคราะห์ frame {c}/{t}"))
    except Exception as e: st.error(f"วิเคราะห์ไม่สำเร็จ: {e}"); return None
    finally: path.unlink(missing_ok=True)
def results(report):
    coach=report["coach"]; inf=coach["inference"]; view=coach["presentation"]; m=report["metrics"]; q=report["quality"]
    st.divider(); st.header("ผลประเมินจาก Virtual Rehab Vibe Coach")
    a,b,c=st.columns(3); a.metric("แขนที่คาดว่าถนัดโดยธรรมชาติ",label(view["predicted_natural_dominance"])); b.metric("แขนที่เลือกใช้ในคลิป",label(view["observed_hand_choice"])); c.metric("ความมั่นใจ",inf["dominance_confidence"].upper())
    st.info(coach["coach_message"])
    hypothesis=view["learned_non_use_hypothesis"].replace('_',' ')
    st.subheader("Learned Non-use Hypothesis"); st.write(hypothesis)
    st.caption("ผลซ้าย/ขวาใช้ทิศตาม label ที่ปรากฏบนวิดีโอ ไม่ใช่ anatomical side ของ MediaPipe")
    st.subheader("Digital biomarkers")
    rows=[]
    for side in ("left","right"):
        rows.append({"แขน":label(side),"Speed":inf[f"{side}_profile"]["speed"],"Trajectory control":inf[f"{side}_profile"]["control"],"Movement quality":inf[f"{side}_profile"]["quality"],"Hesitation":m[f"{side}_hesitation_count"],"Elbow range":m[f"{side}_elbow_range"]})
    st.dataframe(pd.DataFrame(rows).style.format({"Speed":"{:.0f}","Trajectory control":"{:.0f}","Movement quality":"{:.0f}","Elbow range":"{:.1f}"}),hide_index=True,use_container_width=True)
    st.caption(f"Pose quality {q['pose_coverage_pct']:.0f}% | {coach['privacy']}")
    with st.expander("Why this result?"):
        st.write("คะแนน evidence ผสม Speed 40%, trajectory control 30% และ movement quality 30% แล้วเปรียบเทียบกับแขนที่ถูกเลือกใช้จริง")
        st.json({"inference":inf,"metrics":m})
    st.download_button("ดาวน์โหลดรายงาน JSON",report_as_json(report),"virtual_rehab_report.json","application/json")
def main():
    st.markdown("""<section class='hero'><p class='eyebrow'>Secure AI-assisted movement insight</p><h1>Virtual Rehab Vibe Coach</h1><p>เปลี่ยนวิดีโอการเคลื่อนไหวเป็น Digital Biomarkers และคำแนะนำที่เข้าใจง่าย</p></section>""",unsafe_allow_html=True)
    st.subheader("เริ่มการประเมิน"); st.caption("อัปโหลดวิดีโอที่เห็นไหล่ ข้อศอก และข้อมือทั้งสองข้างตลอดกิจกรรม")
    uploaded=st.file_uploader("วิดีโอการใช้แขนอิสระ",type=["mp4","mov","avi"]); consent=st.checkbox("ยืนยันว่าได้รับความยินยอมในการประมวลผลวิดีโอสำหรับเดโมแล้ว")
    if uploaded: st.video(uploaded)
    if st.button("เริ่มวิเคราะห์ด้วย AI Coach",type="primary",use_container_width=True,disabled=not(uploaded and consent)):
        report=analyze(uploaded)
        if report: st.session_state['rehab_report']=report
    if report:=st.session_state.get('rehab_report'): results(report)
if __name__=='__main__': main()
