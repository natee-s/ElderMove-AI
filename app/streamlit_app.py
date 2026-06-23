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
.stApp{background:#f7f8f6;color:#203b38}.block-container{max-width:980px;padding-top:2rem;padding-bottom:4rem}.hero{background:#315c57;border-radius:8px;padding:2.2rem;color:#fff}.hero h1{color:#fff;margin:0;font-size:2.35rem}.hero p{color:#e1efeb;margin:.55rem 0 0;font-size:1.05rem}.eyebrow{color:#bee3d9;font-size:.76rem;font-weight:700;letter-spacing:.08rem;text-transform:uppercase}h2,h3{color:#203b38!important}p,div,span{letter-spacing:0!important}.step{background:#fff;border:1px solid #dbe7e2;border-radius:6px;min-height:116px;padding:1rem}.step b{display:block;color:#267c70;font-size:1.35rem;margin-bottom:.35rem}.step span{font-size:.93rem;color:#49635f;line-height:1.45}.section-label{font-size:.78rem;font-weight:700;color:#267c70;text-transform:uppercase;letter-spacing:.08rem!important;margin-top:2rem}div[data-testid="stMetric"]{background:#fff;border:1px solid #dbe7e2;border-top:4px solid #5a9f91;border-radius:6px;padding:1rem;min-height:118px}div[data-testid="stMetricLabel"]{font-size:1rem;color:#4b6560}div[data-testid="stMetricValue"]{font-size:1.65rem;color:#203b38}button[kind="primary"]{background:#267c70!important;border-color:#267c70!important;border-radius:6px!important;min-height:3.1rem;font-size:1.05rem;font-weight:700}div[data-testid="stFileUploader"]{background:#fff;border:1.5px dashed #8ab8ae;border-radius:6px;padding:.95rem}div[data-testid="stAlert"]{border-radius:6px}div[data-testid="stDataFrame"]{border:1px solid #dbe7e2;border-radius:6px;overflow:hidden}details{background:#fff;border:1px solid #dbe7e2;border-radius:6px;padding:.4rem .7rem}</style>""",unsafe_allow_html=True)

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
    hypothesis = view["learned_non_use_hypothesis"]
    hypothesis_text = {
        "use_matches_prediction": "การเลือกใช้แขนสอดคล้องกับผลประเมิน",
        "uncertain": "ข้อมูลจากคลิปยังไม่ชัดเจนพอ",
        "possible_left_learned_non_use": "ควรให้ผู้เชี่ยวชาญตรวจแขนซ้ายเพิ่มเติม",
        "possible_right_learned_non_use": "ควรให้ผู้เชี่ยวชาญตรวจแขนขวาเพิ่มเติม",
    }.get(hypothesis, "ข้อมูลยังไม่ชัดเจนพอ")
    st.subheader("ข้อสังเกตจากการใช้แขน"); st.write(hypothesis_text)
    st.caption("ผลซ้าย/ขวาใช้ทิศตาม label ที่ปรากฏบนวิดีโอ ไม่ใช่ anatomical side ของ MediaPipe")
    st.subheader("Digital biomarkers")
    rows=[]
    for video_side, anatomical_side in (("left", "right"), ("right", "left")):
        rows.append({"แขน":label(video_side),"ความเร็ว":inf[f"{anatomical_side}_profile"]["speed"],"การควบคุมทิศทาง":inf[f"{anatomical_side}_profile"]["control"],"ความลื่นไหล":inf[f"{anatomical_side}_profile"]["quality"],"ชะงัก":m[f"{anatomical_side}_hesitation_count"],"ช่วงงอข้อศอก":m[f"{anatomical_side}_elbow_range"]})
    st.dataframe(pd.DataFrame(rows).style.format({"ความเร็ว":"{:.0f}","การควบคุมทิศทาง":"{:.0f}","ความลื่นไหล":"{:.0f}","ช่วงงอข้อศอก":"{:.1f}"}),hide_index=True,use_container_width=True)
    st.caption(f"ความชัดเจนของท่าทางในวิดีโอ: {q['pose_coverage_pct']:.0f}%")
    st.download_button("ดาวน์โหลดรายงาน JSON",report_as_json(report),"virtual_rehab_report.json","application/json")
def main():
    st.markdown("""<section class='hero'><p class='eyebrow'>Secure AI-assisted movement insight</p><h1>Virtual Rehab Vibe Coach</h1><p>เปลี่ยนวิดีโอการเคลื่อนไหวเป็น Digital Biomarkers และคำแนะนำที่เข้าใจง่าย</p></section>""",unsafe_allow_html=True)
    st.markdown("<p class='section-label'>ทำตาม 5 ขั้นตอน</p>",unsafe_allow_html=True)
    steps=st.columns(5)
    for column, number, text in zip(steps, ("1","2","3","4","5"), ("อัปโหลดคลิป", "ยืนยันความยินยอม", "ตรวจดูคลิป", "กดเริ่มวิเคราะห์", "อ่านผลสรุป")):
        with column: st.markdown(f"<div class='step'><b>{number}</b><span>{text}</span></div>",unsafe_allow_html=True)
    st.markdown("<p class='section-label'>เริ่มการประเมิน</p>",unsafe_allow_html=True); st.caption("อัปโหลดวิดีโอที่เห็นไหล่ ข้อศอก และข้อมือทั้งสองข้างตลอดกิจกรรม")
    uploaded=st.file_uploader("วิดีโอการใช้แขนอิสระ",type=["mp4","mov","avi"]); consent=st.checkbox("ยืนยันว่าได้รับความยินยอมในการประมวลผลวิดีโอสำหรับเดโมแล้ว")
    if uploaded:
        st.success("อัปโหลดคลิปแล้ว กรุณากดเล่นเพื่อตรวจว่ามองเห็นแขนทั้งสองข้างชัดเจน")
        st.video(uploaded)
    if st.button("เริ่มวิเคราะห์ด้วย AI Coach",type="primary",use_container_width=True,disabled=not(uploaded and consent)):
        report=analyze(uploaded)
        if report: st.session_state['rehab_report']=report
    if report:=st.session_state.get('rehab_report'): results(report)
if __name__=='__main__': main()
