import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REPORTS_PATH = DATA_DIR / "reports.json"


def parse_srt(srt_path):
    """Parse a basic SRT file into a list of subtitle blocks."""
    text = srt_path.read_text(encoding="utf-8", errors="replace")
    entries = []
    blocks = text.strip().split("\n\n")

    for block in blocks:
        if not block.strip():
            continue
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3:
            continue
        entry = {
            "index": lines[0],
            "time": lines[1],
            "text": " ".join(lines[2:]),
        }
        entries.append(entry)

    return entries


def generate_report(video_path, srt_path):
    """Create a structured report summary from a video and subtitle pair."""
    subtitles = parse_srt(srt_path)
    total_words = sum(len(item["text"].split()) for item in subtitles)
    return {
        "report_id": str(uuid4()),
        "video_name": video_path.name,
        "subtitle_name": srt_path.name,
        "subtitle_count": len(subtitles),
        "total_words": total_words,
        "duration_seconds": 0,
        "status": "ready",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def load_reports(path=REPORTS_PATH):
    """Load the saved report history from JSON, returning an empty list if missing."""
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


def save_reports(reports, path=REPORTS_PATH):
    """Persist report history to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(reports, indent=2), encoding="utf-8")


def _render_report_card(report):
    summary = [
        ("Report ID", report.get("report_id", "-")),
        ("Video", report.get("video_name", "-")),
        ("Subtitle", report.get("subtitle_name", "-")),
        ("Subtitles", report.get("subtitle_count", 0)),
        ("Word Count", report.get("total_words", 0)),
        ("Status", report.get("status", "pending")),
        ("Created", report.get("created_at", "-")),
    ]

    st.markdown("### Report summary")
    for label, value in summary:
        st.write(f"**{label}:** {value}")


def _inject_dashboard_css():
    st.markdown(
        """
        <style>
        html, body, [data-testid="stAppViewContainer"], .stApp {
            background: #020d18;
            color: #eaf6ff;
        }
        .block-container {
            padding-top: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            max-width: 100% !important;
        }
        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 56px;
            padding: 0 18px 0 24px;
            border-bottom: 1px solid rgba(120, 180, 220, 0.18);
            background: rgba(1, 14, 24, 0.94);
            margin: 0;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            letter-spacing: 0.22em;
            color: #d9f2ff;
            font-weight: 700;
            text-transform: uppercase;
        }
        .brand-mark {
            width: 16px;
            height: 16px;
            display: inline-block;
            background: linear-gradient(135deg, #40d9ff, #0b5bb5);
            border-radius: 5px;
            box-shadow: 0 0 18px rgba(64, 217, 255, 0.7);
            transform: rotate(45deg);
        }
        .nav-items {
            display: flex;
            gap: 18px;
            align-items: center;
            height: 100%;
        }
        .nav-item {
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 130px;
            height: 100%;
            color: rgba(190, 214, 236, 0.82);
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-size: 12px;
            font-weight: 600;
            border-bottom: 2px solid transparent;
        }
        .nav-item.active {
            color: #6fe8ff;
            border-bottom-color: #38dff7;
        }
        .date-chip {
            text-align: right;
            color: rgba(220, 233, 245, 0.8);
            font-size: 12px;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }
        .page {
            padding: 22px 30px 16px 30px;
            min-height: calc(100vh - 56px);
            background: #020d18;
        }
        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 6px 0 6px 0;
        }
        .section-title {
            color: #b3d0ea;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.22em;
            text-transform: uppercase;
            margin: 0;
        }
        .primary-button {
            background: linear-gradient(180deg, #41dbff 0%, #1dc8ef 100%);
            color: #041827;
            border: none;
            border-radius: 10px;
            padding: 0.7rem 1.2rem;
            font-weight: 700;
            font-size: 14px;
            letter-spacing: 0.04em;
            box-shadow: 0 0 0 1px rgba(38, 163, 222, 0.6);
        }
        .primary-button:hover {
            filter: brightness(1.05);
        }
        .primary-button > button {
            background: linear-gradient(180deg, #41dbff 0%, #1dc8ef 100%) !important;
            color: #041827 !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            height: 52px !important;
            box-shadow: none !important;
        }
        .empty-state {
            min-height: 420px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 12px;
            text-align: center;
            color: #bbd3e7;
            padding-top: 18px;
        }
        .empty-icon {
            width: 68px;
            height: 68px;
            border: 2px solid rgba(119, 167, 205, 0.6);
            border-radius: 18px;
            transform: rotate(45deg);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 4px;
            background: rgba(24, 61, 85, 0.08);
        }
        .empty-icon::before {
            content: "+";
            transform: rotate(-45deg);
            font-size: 34px;
            color: rgba(126, 174, 212, 0.8);
        }
        .empty-title {
            font-size: 20px;
            font-weight: 600;
            letter-spacing: 0.02em;
            color: #dfeaf8;
        }
        .empty-copy {
            max-width: 510px;
            font-size: 15px;
            color: rgba(191, 213, 233, 0.72);
            line-height: 1.7;
        }
        .empty-button {
            margin-top: 10px;
        }
        .modal-shell {
            margin: 18px auto 12px auto;
            max-width: 1100px;
            background: rgba(2, 17, 28, 0.96);
            border: 1px solid rgba(91, 143, 181, 0.18);
            border-radius: 10px;
            padding: 18px 22px 14px 22px;
            box-shadow: 0 14px 40px rgba(0, 0, 0, 0.28);
        }
        .modal-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 0 0 18px 0;
            padding-top: 4px;
        }
        .modal-title {
            color: #dff9ff;
            font-size: 14px;
            letter-spacing: 0.22em;
            text-transform: uppercase;
            font-weight: 700;
        }
        .close-btn {
            background: transparent !important;
            border: none !important;
            color: rgba(195, 220, 240, 0.8) !important;
            font-size: 34px !important;
            line-height: 1 !important;
            padding: 0 !important;
            min-width: 20px !important;
            width: 20px !important;
        }
        .section-label {
            color: #4ecff5;
            font-size: 11px;
            letter-spacing: 0.22em;
            text-transform: uppercase;
            font-weight: 700;
            margin: 18px 0 14px 0;
        }
        .upload-box {
            border: 1px dashed rgba(71, 169, 221, 0.6) !important;
            border-radius: 8px !important;
            background: rgba(7, 21, 30, 0.6) !important;
            min-height: 113px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        [data-testid="stFileUploader"] section {
            border: 1px dashed rgba(71, 169, 221, 0.6) !important;
            border-radius: 8px !important;
            background: rgba(7, 21, 30, 0.6) !important;
            min-height: 112px !important;
        }
        [data-testid="stFileUploader"] label {
            color: rgba(208, 232, 247, 0.72) !important;
            font-size: 14px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.12em !important;
            font-weight: 600 !important;
        }
        [data-testid="stFileUploader"] .stFileUploaderFileName {
            color: #dff7ff !important;
        }
        .param-row {
            display: flex;
            gap: 1rem;
            align-items: flex-end;
        }
        .stSelectbox > div, .stDateInput > div, .stTimeInput > div {
            background: rgba(4, 16, 25, 0.8) !important;
            border: 1px solid rgba(126, 148, 176, 0.42) !important;
            border-radius: 8px !important;
            color: #ecf8ff !important;
            min-height: 52px !important;
        }
        .stSlider {
            padding-top: 10px;
            margin-top: 6px;
        }
        .stSlider [data-testid="stBaseWidgetLabel"] {
            color: #bfe5f9 !important;
            font-size: 11px !important;
            letter-spacing: 0.22em !important;
            text-transform: uppercase !important;
            font-weight: 700 !important;
        }
        .stSlider .stMarkdownContainer {
            color: rgba(204, 224, 239, 0.7) !important;
            font-size: 11px !important;
            letter-spacing: 0.08em !important;
        }
        .stSlider .stSliderTrack {
            background: rgba(127, 159, 181, 0.35) !important;
        }
        .stSlider [data-testid="stThumbValue"] {
            color: #081b2b !important;
        }
        .stSlider [data-testid="stSliderThumb"] {
            background: linear-gradient(180deg, #44d9ff 0%, #2bbfee 100%) !important;
            border: 2px solid #a7f0ff !important;
        }
        .stButton > button {
            background: linear-gradient(180deg, #41dbff 0%, #1dc8ef 100%) !important;
            color: #041827 !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
            padding: 0.65rem 1.1rem !important;
        }
        .close-btn button {
            background: transparent !important;
            border: none !important;
            color: rgba(195, 220, 240, 0.8) !important;
            font-size: 28px !important;
            padding: 0 !important;
        }
        @media (max-width: 900px) {
            .nav-item {
                min-width: 90px;
                letter-spacing: 0.08em;
                font-size: 10px;
            }
            .stForm {
                width: 92vw !important;
                left: 50% !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_report_list(reports):
    if not reports:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-icon"></div>
                <div class="empty-title">No inspection reports</div>
                <div class="empty-copy">Upload a drone video and SRT file to generate first report.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("+ New Report", key="empty_new_report"):
            st.session_state.show_new_report = True
        return

    for report in reports:
        st.markdown(
            f"""
            <div style="padding: 18px 18px; border: 1px solid rgba(99, 154, 192, 0.25); border-radius: 10px; margin-bottom: 12px; background: rgba(9, 21, 31, 0.55);">
                <div style="display:flex; justify-content:space-between; align-items:center; color:#dfeefb; font-weight:700; letter-spacing:0.08em; text-transform:uppercase;">
                    <span>{report.get('video_name', 'Unnamed video')}</span>
                    <span style="color:#66dfff; font-size:11px;">{report.get('status', 'ready').upper()}</span>
                </div>
                <div style="margin-top: 14px; color: rgba(198, 218, 236, 0.74); font-size: 13px; line-height: 1.8;">
                    <div>Subtitle file: {report.get('subtitle_name', '-')}</div>
                    <div>Subtitle count: {report.get('subtitle_count', 0)}</div>
                    <div>Word count: {report.get('total_words', 0)}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def main():
    st.set_page_config(page_title="DroneView Inspect", page_icon="◫", layout="wide")
    _inject_dashboard_css()

    if "reports" not in st.session_state:
        st.session_state.reports = load_reports()
    if "show_new_report" not in st.session_state:
        st.session_state.show_new_report = False

    st.markdown(
        """
        <div class="topbar">
            <div class="brand"><span class="brand-mark"></span><span>DRONEVIEW</span><span style="color:#7ddafc; letter-spacing:0.14em;">INSPECT</span></div>
            <div class="nav-items">
                <div class="nav-item active">Reports</div>
                <div class="nav-item">Video Library</div>
            </div>
            <div class="date-chip">14 Aug 2026</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="page">', unsafe_allow_html=True)

    report_header_col, action_col = st.columns([4, 1.1])
    with report_header_col:
        st.markdown(
            '<div class="section-title">Inspection Reports</div>',
            unsafe_allow_html=True,
        )
    with action_col:
        if st.button("+ New Report", key="top_new_report"):
            st.session_state.show_new_report = True

    if st.session_state.show_new_report:
        st.markdown('<div class="modal-shell">', unsafe_allow_html=True)
        with st.form("new_report_form", clear_on_submit=True):
            header_col, close_col = st.columns([8, 1])
            with header_col:
                st.markdown(
                    """
                    <div class="modal-title">New Inspection Report</div>
                    """,
                    unsafe_allow_html=True,
                )
                st.caption("Upload media and configure processing parameters")
            with close_col:
                if st.button("✕", key="close_modal_btn", help="Close"):
                    st.session_state.show_new_report = False
                    st.rerun()

            st.markdown(
                '<div class="section-label">Media Upload</div>', unsafe_allow_html=True
            )
            video_file = st.file_uploader(
                "VIDEO FILE (.mp4)",
                type=["mp4"],
                label_visibility="collapsed",
                key="video_upload",
            )
            telemetry_file = st.file_uploader(
                "TELEMETRY DATA (.srt)",
                type=["srt"],
                label_visibility="collapsed",
                key="telemetry_upload",
            )

            st.markdown(
                '<div class="section-label">Configuration Parameters</div>',
                unsafe_allow_html=True,
            )
            uav_id = st.selectbox("UAV ID", options=["15001"], index=0)

            clear_col1, clear_col2 = st.columns(2)
            with clear_col1:
                clearance_distance = st.selectbox(
                    "SAFE CLEARANCE DISTANCE (m)", options=["0 - 200"], index=0
                )
            with clear_col2:
                clearance_height = st.selectbox(
                    "CLEARANCE HEIGHT (m)", options=["0 - 100"], index=0
                )

            date_col, time_col = st.columns(2)
            with date_col:
                inspection_date = st.date_input(
                    "INSPECTION DATE & TIME", value=datetime.now().date()
                )
            with time_col:
                inspection_time = st.time_input("", value=datetime.now().time())

            sensitivity = st.slider(
                "SENSITIVITY", min_value=1, max_value=10, value=5, step=1
            )

            submitted = st.form_submit_button(
                "Generate Report", use_container_width=True
            )
            if submitted:
                if video_file is None or telemetry_file is None:
                    st.warning("Please upload both the drone video and the SRT file.")
                else:
                    temp_dir = DATA_DIR / "uploads"
                    temp_dir.mkdir(parents=True, exist_ok=True)
                    video_path = temp_dir / video_file.name
                    subtitle_path = temp_dir / telemetry_file.name
                    video_path.write_bytes(video_file.getvalue())
                    subtitle_path.write_text(
                        telemetry_file.getvalue().decode("utf-8", errors="replace"),
                        encoding="utf-8",
                    )
                    report = generate_report(video_path, subtitle_path)
                    report["uav_id"] = uav_id
                    report["clearance_distance"] = clearance_distance
                    report["clearance_height"] = clearance_height
                    report["inspection_date"] = inspection_date.isoformat()
                    report["inspection_time"] = inspection_time.strftime("%H:%M")
                    report["sensitivity"] = sensitivity
                    st.session_state.reports.insert(0, report)
                    save_reports(st.session_state.reports)
                    st.session_state.show_new_report = False
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    _render_report_list(st.session_state.reports)

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
