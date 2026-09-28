from __future__ import annotations

import os
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

import streamlit as st

if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = str(st.secrets["GEMINI_API_KEY"])
if "GEMINI_MODEL" in st.secrets:
    os.environ["GEMINI_MODEL"] = str(st.secrets["GEMINI_MODEL"])

from src.ai_engine import extract_report_data
from src.file_extract import extract_document
from src.report_generator import generate_event_report, generate_iqac_summary

st.set_page_config(
    page_title="IQAC Report Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .hero{padding:1.15rem 0 .8rem 0}.hero h1{font-size:2.15rem;letter-spacing:-.03em;margin:0}
    .hero p{color:#6b7280;margin:.35rem 0 0 0;font-size:1rem}
    .step{font-size:.82rem;font-weight:600;color:#6b7280}
    .small{font-size:.85rem;color:#6b7280}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="hero"><h1>📄 IQAC Report Generator</h1><p>Prepare your official Event Report and IQAC Summary Report from the documents you already have.</p></div>', unsafe_allow_html=True)
st.divider()

if "data" not in st.session_state:
    st.session_state.data = None
if "generated" not in st.session_state:
    st.session_state.generated = None

c1, c2, c3, c4 = st.columns(4)
for col, num, label in [(c1,"1","Upload"),(c2,"2","AI Extract"),(c3,"3","Review"),(c4,"4","Generate")]:
    with col:
        st.markdown(f'<div class="step">{num} · {label}</div>', unsafe_allow_html=True)

st.subheader("1. Upload activity documents")
left, right = st.columns(2, gap="large")
with left:
    notice_files = st.file_uploader("Notice", type=["pdf","docx","txt","xlsx","xlsm","jpg","jpeg","png","webp"], accept_multiple_files=True, key="notice")
    proposal_files = st.file_uploader("Proposal", type=["pdf","docx","txt","xlsx","xlsm","jpg","jpeg","png","webp"], accept_multiple_files=True, key="proposal")
    invitation_files = st.file_uploader("Letter of Invitation / Appreciation (optional)", type=["pdf","docx","txt","jpg","jpeg","png","webp"], accept_multiple_files=True, key="invitation")
    other_files = st.file_uploader("Other supporting documents (optional)", type=["pdf","docx","txt","xlsx","xlsm","jpg","jpeg","png","webp"], accept_multiple_files=True, key="other")
with right:
    geo_files = st.file_uploader("Geotagged photographs", type=["jpg","jpeg","png","webp"], accept_multiple_files=True, key="geo")
    normal_files = st.file_uploader("Normal photographs", type=["jpg","jpeg","png","webp"], accept_multiple_files=True, key="normal")
    news_files = st.file_uploader("News photograph(s)", type=["jpg","jpeg","png","webp"], accept_multiple_files=True, key="news")

all_required_files = bool(notice_files or proposal_files)
if not all_required_files:
    st.info("Upload at least a Notice or Proposal. Add the invitation/appreciation letter when available so the Resource Person can be identified automatically.")

if st.button("✨ Extract Activity Details", type="primary", use_container_width=True, disabled=not all_required_files):
    if not os.getenv("GEMINI_API_KEY"):
        st.error("GEMINI_API_KEY is not configured. Add it to Streamlit Secrets before extraction.")
        st.stop()
    with st.spinner("Reading documents and preparing the report fields…"):
        docs = []
        vision_images = []
        input_groups = [
            notice_files or [], proposal_files or [], invitation_files or [], other_files or []
        ]
        for group in input_groups:
            for f in group:
                parsed, imgs = extract_document(f.name, f.getvalue())
                docs.append(parsed)
                vision_images.extend(imgs)
        result = extract_report_data(docs, vision_images)
        st.session_state.data = result.model_dump()
        st.session_state.generated = None
    st.success("Activity details extracted. Review the fields below before generating the reports.")

if st.session_state.data:
    st.subheader("2. Review extracted details")
    data = st.session_state.data
    a, b = st.columns(2)
    with a:
        data["title"] = st.text_input("Activity Title", data.get("title", ""))
        data["activity_date"] = st.text_input("Activity Date", data.get("activity_date", ""))
        data["time"] = st.text_input("Time", data.get("time", ""))
        data["venue"] = st.text_input("Venue", data.get("venue", ""))
        data["department_committee_association"] = st.text_input("Department / Committee / Association", data.get("department_committee_association", ""))
        data["activity_type"] = st.text_input("Type of Activity", data.get("activity_type", ""))
        data["resource_person"] = st.text_input("Resource Person", data.get("resource_person", ""))
    with b:
        data["faculty"] = st.text_input("Faculty", data.get("faculty", ""))
        data["participants"] = st.text_input("No. of Participants", data.get("participants", ""))
        data["coordinator_name_phone"] = st.text_input("Coordinator's Name & Phone", data.get("coordinator_name_phone", ""))
        data["invited_guest"] = st.text_input("Invited Guest", data.get("invited_guest", ""))
        data["proposal_date"] = st.text_input("Date of Proposal", data.get("proposal_date", ""))
        data["activity_schedule_number"] = st.text_input("Activity Schedule Number", data.get("activity_schedule_number", ""))
    data["brief_information"] = st.text_area("Brief Information", data.get("brief_information", ""), height=90)
    d1, d2 = st.columns(2)
    with d1:
        data["profile_topic"] = st.text_area("Profile / Topic / Subject", data.get("profile_topic", ""), height=90)
        data["objective"] = st.text_area("Objectives", data.get("objective", ""), height=100)
        data["methodology"] = st.text_area("Methodology", data.get("methodology", ""), height=80)
    with d2:
        data["outcome"] = st.text_area("Outcome", data.get("outcome", ""), height=100)
        data["activity_for_class_group"] = st.text_input("Activity for Class / Group", data.get("activity_for_class_group", ""))
        data["members_support"] = st.text_area("Members / Support", data.get("members_support", ""), height=80)
    data["event_report"] = st.text_area("Event Report (100–150 words)", data.get("event_report", ""), height=160)
    st.session_state.data = data

    with st.expander("Detected supporting documents", expanded=False):
        detected = []
        for name, flag in [
            ("Proposal", data.get("proposal_present")),
            ("Notice", data.get("notice_present")),
            ("Programme / Schedule", data.get("programme_present")),
            ("Invitation / Appreciation", data.get("invitation_present")),
            ("Attendance", data.get("attendance_present")),
            ("Event Report / Geotagged Photo Evidence", data.get("event_report_evidence_present")),
            ("Feedback", data.get("feedback_present")),
            ("News", data.get("news_present")),
            ("Publicity", data.get("publicity_present")),
            ("Certificate", data.get("certificate_present")),
            ("Other Evidence", data.get("other_evidence_present")),
        ]:
            if flag:
                detected.append(name)
        st.write(", ".join(detected) if detected else "No supporting evidence was identified yet.")

    st.subheader("3. Generate reports")
    st.caption("The supplied official Word templates are used as-is. Existing formatting, tables, signatures and page structure are preserved; only data, proof ticks and photo areas are populated.")

    if st.button("🚀 Generate Event Report + IQAC Summary Report", type="primary", use_container_width=True):
        with st.spinner("Filling the official templates…"):
            tmp = Path(tempfile.mkdtemp(prefix="iqac_report_gen_"))
            geo = [f.getvalue() for f in (geo_files or [])]
            normal = [f.getvalue() for f in (normal_files or [])]
            news = [f.getvalue() for f in (news_files or [])]
            event_bytes, event_name = generate_event_report(
                str(BASE_DIR / "templates/Event report with geotagged photos and news.docx"),
                data,
                geo,
                normal,
                news,
                tmp,
            )

            def names(files):
                return [f.name.lower() for f in (files or [])]

            other_names = names(other_files)
            known_markers = (
                "program", "programme", "schedule", "invitation", "appreciation",
                "attendance", "participant", "feedback", "news", "publicity", "reel",
                "social", "certificate", "proposal", "notice", "event report", "event_report"
            )
            unknown_other_upload = any(not any(marker in name for marker in known_markers) for name in other_names)
            proof_flags = {
                "proposal": bool(proposal_files) or bool(data.get("proposal_present")),
                "notice": bool(notice_files) or bool(data.get("notice_present")),
                "programme": bool(data.get("programme_present")) or any("program" in n or "programme" in n or "schedule" in n for n in other_names),
                "invitation": bool(invitation_files) or bool(data.get("invitation_present")) or any("invitation" in n or "appreciation" in n for n in other_names),
                "attendance": bool(data.get("attendance_present")) or any("attendance" in n or "participant" in n for n in other_names),
                "event_report_evidence": bool(geo) or bool(data.get("event_report_evidence_present")),
                "feedback": bool(data.get("feedback_present")) or any("feedback" in n for n in other_names),
                "news": bool(news) or bool(data.get("news_present")) or any("news" in n for n in other_names),
                "publicity": bool(data.get("publicity_present")) or any("publicity" in n or "reel" in n or "social" in n for n in other_names),
                "certificate": bool(data.get("certificate_present")) or any("certificate" in n for n in other_names),
                "other": bool(data.get("other_evidence_present")) or unknown_other_upload,
            }
            summary_bytes, summary_name = generate_iqac_summary(
                str(BASE_DIR / "templates/Revised IQAC Report Format 2026-27.docx"),
                data,
                proof_flags,
            )
            st.session_state.generated = {
                "event": (event_bytes, event_name),
                "summary": (summary_bytes, summary_name),
            }
        st.success("Both editable Word reports are ready.")

if st.session_state.generated:
    st.subheader("4. Download")
    e, s = st.columns(2)
    with e:
        st.download_button("⬇️ Event Report (.docx)", st.session_state.generated["event"][0], file_name=st.session_state.generated["event"][1], mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    with s:
        st.download_button("⬇️ IQAC Summary Report (.docx)", st.session_state.generated["summary"][0], file_name=st.session_state.generated["summary"][1], mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)

st.divider()
st.caption("AI-assisted document preparation. Review the generated Word files before official submission.")
