"""
RoW Inspection Reports Table
-----------------------------
Requires Streamlit >= 1.35 (uses `index=None` on st.selectbox and
`value=None` on st.number_input to represent "not yet filled in").

Features:
- "New Report" popover: upload MP4 + SRT, set UAV/processing params.
    - "Start Processing" is disabled until every field is filled in.
    - "Cancel" asks for confirmation before discarding the form.
      NOTE: Streamlit has no callback for "user clicked outside the
      popover to dismiss it" — only the explicit Cancel button can be
      intercepted with a confirmation prompt.
    - On successful "Start Processing", the popover auto-closes.
- Table columns: Filename, UAV ID, Inspection Date Time,
  Safe Clearance Distance (m), Clearance Height (m), Sensitivity, Status
    - Status shown as a colored badge: blue=Queued, orange=Processing,
      green=Completed, red=Failed.
    - Filename search box, plus a Filters & Sort panel covering every
      column (multiselect, range, date-range, sort-by + order).
- Click a filename -> popup (st.dialog) previews the rendered HTML report.
- Check one or more rows -> download button appears (zipped if 2+).

Run with: streamlit run app.py
"""

import io
import shutil
import zipfile
import uuid
from datetime import datetime, timezone

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="RoW Inspection Reports", layout="wide")

# ---------------------------------------------------------------------------
# Session state setup
# ---------------------------------------------------------------------------
if "reports" not in st.session_state:
    st.session_state.reports = []  # list of dicts, newest first

if "selected" not in st.session_state:
    st.session_state.selected = {}

if "form_key" not in st.session_state:
    # bumped after cancel/submit to reset the popover's widgets
    st.session_state.form_key = 0

if "popover_open" not in st.session_state:
    # controls whether the real st.popover element is mounted at all;
    # remounting it fresh is how we force it to appear "closed"
    st.session_state.popover_open = True

if "confirm_cancel" not in st.session_state:
    st.session_state.confirm_cancel = False

if "preview_report_id" not in st.session_state:
    st.session_state.preview_report_id = None

if "preview_seek" not in st.session_state:
    st.session_state.preview_seek = 0


def inject_preview_drawer_css():
    """
    Best-effort CSS to turn Streamlit's centered st.dialog into a right-side
    drawer occupying ~2/3 of the viewport width and the full height.

    CAVEAT: this relies on Streamlit's *undocumented* internal dialog DOM
    (the data-testid="stDialog" overlay + its child panel). It was written
    against Streamlit >= 1.35 and MAY BREAK on other versions. If the drawer
    stops sliding in from the side after a Streamlit upgrade, open browser
    devtools, inspect the dialog element, and update the selectors below.
    """
    st.markdown(
        """
        <style>
        div[data-testid="stDialog"] {
            align-items: stretch !important;
            justify-content: flex-end !important;
        }
        div[data-testid="stDialog"] > div {
            width: 66vw !important;
            max-width: 66vw !important;
            height: 100vh !important;
            max-height: 100vh !important;
            margin: 0 !important;
            border-radius: 0 !important;
            animation: rowPreviewSlideIn 0.22s ease-out;
        }
        @keyframes rowPreviewSlideIn {
            from { transform: translateX(100%); }
            to   { transform: translateX(0); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_mmss(seconds: int) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


STATUS_COLORS = {
    "Queued": "#1E88E5",      # blue
    "Processing": "#FB8C00",  # orange
    "Completed": "#43A047",   # green
    "Failed": "#E53935",      # red
}
STATUS_OPTIONS = list(STATUS_COLORS.keys())


def status_badge_html(status: str) -> str:
    color = STATUS_COLORS.get(status, "#757575")
    return (
        f'<span style="background-color:{color}; color:white; padding:3px 12px; '
        f'border-radius:12px; font-size:0.85em; font-weight:600; white-space:nowrap;">'
        f'{status}</span>'
    )


def make_filename(uav_id: str, inspection_dt: datetime, safe_clearance, clearance_height, sensitivity) -> str:
    date_str = inspection_dt.strftime("%Y-%m-%d")
    time_str = inspection_dt.strftime("%H%M%S")
    return f"{uav_id}_{date_str}_{time_str}_{safe_clearance}m_{clearance_height}m_{sensitivity}"


def generate_report_html(report: dict) -> bytes:
    """Placeholder report generator. Replace with a call to your real AI
    engine / report pipeline, which should return the actual HTML bytes."""
    html = f"""
    <html>
    <head><meta charset="utf-8"><title>{report['Filename']}</title></head>
    <body style="font-family: sans-serif; padding: 24px;">
        <h1>RoW Inspection Report</h1>
        <table style="border-collapse: collapse;">
            <tr><td style="padding:4px 12px;"><b>Filename</b></td><td>{report['Filename']}</td></tr>
            <tr><td style="padding:4px 12px;"><b>Source video</b></td><td>{report['video_name']}</td></tr>
            <tr><td style="padding:4px 12px;"><b>Source SRT</b></td><td>{report['srt_name']}</td></tr>
            <tr><td style="padding:4px 12px;"><b>UAV ID</b></td><td>{report['UAV ID']}</td></tr>
            <tr><td style="padding:4px 12px;"><b>Inspection Date Time</b></td><td>{report['Inspection Date Time']}</td></tr>
            <tr><td style="padding:4px 12px;"><b>Safe Clearance Distance (m)</b></td><td>{report['Safe Clearance Distance (m)']}</td></tr>
            <tr><td style="padding:4px 12px;"><b>Clearance Height (m)</b></td><td>{report['Clearance Height (m)']}</td></tr>
            <tr><td style="padding:4px 12px;"><b>Sensitivity</b></td><td>{report['Sensitivity']}</td></tr>
        </table>
        <p style="margin-top:24px; color:#888;">Placeholder report — wire this up to the real inspection pipeline output.</p>
    </body>
    </html>
    """
    return html.encode("utf-8")

import streamlit as st
import streamlit.components.v1 as components
import base64


def video_player(video_bytes, timestamps):

    video_b64 = base64.b64encode(video_bytes).decode()

    timestamp_buttons = ""

    for i, ts in enumerate(sorted(timestamps, key=lambda t: t["seconds"])):
        seconds = ts["seconds"]
        label = ts["label"]

        timestamp_buttons += f"""
        <button
            onclick="seekVideo({seconds})"
            style="
                display:block;
                width:100%;
                margin:5px 0;
                padding:8px;
                text-align:left;
                border:1px solid #ddd;
                border-radius:6px;
                background:#f8f9fa;
                cursor:pointer;
            "
        >
            ⏱ {format_mmss(seconds)} — {label}
        </button>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <body>

        <video
            id="videoPlayer"
            controls
            width="100%"
            style="max-height:500px;"
        >
            <source
                src="data:video/mp4;base64,{video_b64}"
                type="video/mp4"
            >
        </video>

        <h4>Critical Timestamps</h4>

        {timestamp_buttons}

        <script>
            function seekVideo(seconds) {{
                const video = document.getElementById("videoPlayer");

                video.currentTime = seconds;
                video.play();
            }}
        </script>

    </body>
    </html>
    """

    components.html(
        html,
        height=700,
        scrolling=True,
    )

   
# ---------------------------------------------------------------------------
# Preview popup (side drawer, ~2/3 width) with Report / Processed Video tabs
# ---------------------------------------------------------------------------
@st.dialog("Preview", width="large")
def preview_dialog(report_id: str):
    inject_preview_drawer_css()

    report = next(r for r in st.session_state.reports if r["id"] == report_id)

    # Reset the video seek position whenever a *different* report is opened
    if st.session_state.preview_report_id != report_id:
        st.session_state.preview_report_id = report_id
        st.session_state.preview_seek = 0

    st.caption(report["Filename"])

    if report["Status"] != "Completed":
        st.info(f"Report status: {report['Status']} — no preview available yet.")
        return

    tab_report, tab_video = st.tabs(["📄 Report", "🎬 Processed Video"])

    with tab_report:
        components.html(
            report["html_bytes"].decode("utf-8", errors="replace"),
            height=550,
            scrolling=True,
        )
        st.download_button(
            "⬇ Download report",
            data=report["html_bytes"],
            file_name=report["Filename"],
            mime="text/html",
            key=f"dl_report_{report_id}",
        )

    with tab_video:

        timestamps = report.get("critical_timestamps", [])

        video_player(
            report["video_bytes"],
            timestamps
        )

        st.download_button(
            "⬇ Download video",
            data=report["video_bytes"],
            file_name=report["video_name"],
            mime="video/mp4",
            key=f"dl_video_{report_id}",
        )


# ---------------------------------------------------------------------------
# Header + New Report popover
# ---------------------------------------------------------------------------
st.title("RoW Inspection Reports")

if st.session_state.popover_open:
    with st.popover("➕ New Report"):
        st.write("NEW INSPECTION REPORT")

        if st.session_state.confirm_cancel:
            # ---- Confirmation step, replaces the form ----
            st.warning("Discard this report? Uploaded files and entered values will be lost.")
            yes_col, no_col = st.columns(2)
            if yes_col.button("Yes, cancel", key="confirm_yes", use_container_width=True):
                st.session_state.confirm_cancel = False
                st.session_state.form_key += 1  # reset form fields for next time
                st.rerun()
            if no_col.button("No, go back", key="confirm_no", use_container_width=True):
                st.session_state.confirm_cancel = False
                st.rerun()

        else:
            # ---- Normal form ----
            st.write("Upload media and configure processing parameters")

            fk = st.session_state.form_key
            uploaded_video = st.file_uploader("Choose a MP4 file", type="mp4", key=f"video_{fk}")
            uploaded_srt = st.file_uploader("Choose a SRT file", type="srt", key=f"srt_{fk}")
            uav = ["15005", "16001"]
            selected_id = st.selectbox(
                "UAV ID", uav, index=None, placeholder="Select UAV ID", key=f"uav_{fk}"
            )
            safe_clearance = st.number_input(
                "Safe Clearance Distance (m)", min_value=0, max_value=200, value=None, key=f"sc_{fk}"
            )
            clearance_height = st.number_input(
                "Clearance Height (m)", min_value=0, max_value=200, value=None, key=f"ch_{fk}"
            )
            inspection_dt = st.datetime_input("Inspection Date Time", value=None, key=f"dt_{fk}")
            sensitivity = st.slider("Sensitivity", min_value=1, max_value=10, key=f"sens_{fk}")

            all_filled = all([
                uploaded_video is not None,
                uploaded_srt is not None,
                selected_id is not None,
                safe_clearance is not None,
                clearance_height is not None,
                inspection_dt is not None,
            ])
            if not all_filled:
                st.caption("Fill in every field to enable Start Processing.")

            col1, col2 = st.columns(2)
            cancel = col1.button("Cancel", key=f"cancel_{fk}", use_container_width=True)
            start = col2.button(
                "Start Processing", key=f"start_{fk}", use_container_width=True,
                disabled=not all_filled, type="primary",
            )
                
            if cancel:
                st.session_state.confirm_cancel = True
                st.rerun()

            if start:
                report_id = str(uuid.uuid4())
                inspection_dt_utc = inspection_dt.replace(tzinfo=timezone.utc)
                filename = make_filename(selected_id, inspection_dt_utc, safe_clearance, clearance_height, sensitivity)
                shutil.move("/home/gve/Downloads/videoplayback.mp4", f"/home/gve/Documents/EGAT/EGAT/sample_data/{filename}.mp4")
                
                report = {
                    "id": report_id,
                    "Filename": filename,
                    "UAV ID": selected_id,
                    "Inspection Date Time": inspection_dt_utc,
                    "Safe Clearance Distance (m)": str(safe_clearance),
                    "Clearance Height (m)": str(clearance_height),
                    "Sensitivity": str(sensitivity),
                    "Status": "Completed",
                    "video_name": uploaded_video.name,
                    "srt_name": uploaded_srt.name,
                    "video_bytes": uploaded_video.getvalue(),
                    "srt_bytes": uploaded_srt.getvalue(),
                    # Placeholder events — replace with the actual detected
                    # timestamps (e.g. vegetation encroachment, clearance
                    # violations) returned by your AI engine / report pipeline.
                    "critical_timestamps": [
                        {"seconds": 5, "label": "Vegetation encroachment"},
                        {"seconds": 18, "label": "Clearance violation"},
                        {"seconds": 34, "label": "Optical flow anomaly"},
                    ],
                }
                # Simulate processing completing immediately. For a real
                # async pipeline: set Status="Queued"/"Processing" here,
                # insert the row, and flip it to "Completed" (generating
                # html_bytes then) once your engine actually finishes.
                report["html_bytes"] = generate_report_html(report)

                st.session_state.reports.insert(0, report)
                st.session_state.selected[report_id] = False
                st.session_state.form_key += 1     # reset form fields
                st.session_state.popover_open = False  # force popover closed
                st.success(f"Report '{filename}' created.")
                st.rerun()
else:
    if st.button("➕ New Report"):
        st.session_state.popover_open = True
        st.rerun()

st.divider()

if not st.session_state.reports:
    st.info("No reports yet. Click **New Report** to upload media and generate one.")
    st.stop()

# ---------------------------------------------------------------------------
# Search + Filters & Sort
# ---------------------------------------------------------------------------
search_term = st.text_input("🔍 Search filename", placeholder="Type part of a filename...")

all_uav_ids = sorted({r["UAV ID"] for r in st.session_state.reports})
all_dates = [r["Inspection Date Time"].date() for r in st.session_state.reports]
min_date, max_date = min(all_dates), max(all_dates)

with st.expander("Filters & Sort"):
    fc1, fc2, fc3 = st.columns(3)
    uav_filter = fc1.multiselect("UAV ID", options=all_uav_ids, default=all_uav_ids)
    status_filter = fc2.multiselect("Status", options=STATUS_OPTIONS, default=STATUS_OPTIONS)
    date_range = fc3.date_input(
        "Inspection Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    fc4, fc5, fc6 = st.columns(3)
    safe_range = fc4.slider("Safe Clearance Distance (m)", min_value=0, max_value=200, value=(0, 200))
    height_range = fc5.slider("Clearance Height (m)", min_value=0, max_value=200, value=(0, 200))
    sens_range = fc6.slider("Sensitivity", min_value=1, max_value=10, value=(1, 10))

    fc7, fc8 = st.columns(2)
    sort_by = fc7.selectbox(
        "Sort by",
        options=["Filename", "UAV ID", "Inspection Date Time", "Safe Clearance Distance (m)",
                 "Clearance Height (m)", "Sensitivity", "Status"],
        index=2,
    )
    sort_order = fc8.radio("Order", options=["Descending", "Ascending"], horizontal=True)

# Normalize date_range to a (start, end) pair even mid-selection
if isinstance(date_range, tuple) and len(date_range) == 2:
    date_start, date_end = date_range
else:
    date_start, date_end = min_date, max_date

# ---------------------------------------------------------------------------
# Apply search + filters
# ---------------------------------------------------------------------------
def matches(r: dict) -> bool:
    if search_term and search_term.lower() not in r["Filename"].lower():
        return False
    if r["UAV ID"] not in uav_filter:
        return False
    if r["Status"] not in status_filter:
        return False
    r_date = r["Inspection Date Time"].date()
    if not (date_start <= r_date <= date_end):
        return False
    if not (safe_range[0] <= int(r["Safe Clearance Distance (m)"]) <= safe_range[1]):
        return False
    if not (height_range[0] <= int(r["Clearance Height (m)"]) <= height_range[1]):
        return False
    if not (sens_range[0] <= int(r["Sensitivity"]) <= sens_range[1]):
        return False
    return True


filtered = [r for r in st.session_state.reports if matches(r)]

SORT_KEYS = {
    "Filename": lambda r: r["Filename"].lower(),
    "UAV ID": lambda r: r["UAV ID"],
    "Inspection Date Time": lambda r: r["Inspection Date Time"],
    "Safe Clearance Distance (m)": lambda r: int(r["Safe Clearance Distance (m)"]),
    "Clearance Height (m)": lambda r: int(r["Clearance Height (m)"]),
    "Sensitivity": lambda r: int(r["Sensitivity"]),
    "Status": lambda r: r["Status"],
}
filtered.sort(key=SORT_KEYS[sort_by], reverse=(sort_order == "Descending"))

st.caption(f"Showing {len(filtered)} of {len(st.session_state.reports)} report(s).")

if not filtered:
    st.info("No reports match the current search/filters.")
    st.stop()

# ---------------------------------------------------------------------------
# Table header
# ---------------------------------------------------------------------------
COL_WEIGHTS = [0.4, 3, 0.7, 1.8, 1.5, 1.3, 0.9, 1.1]
(col_check, col_name, col_uav, col_time,
 col_safe, col_height, col_sens, col_status) = st.columns(COL_WEIGHTS)

col_check.markdown("**Select**")
col_name.markdown("**Filename**")
col_uav.markdown("**UAV ID**")
col_time.markdown("**Inspection Date Time**")
col_safe.markdown("**Safe Clearance (m)**")
col_height.markdown("**Clearance Height (m)**")
col_sens.markdown("**Sensitivity**")
col_status.markdown("**Status**")

# ---------------------------------------------------------------------------
# Table rows
# ---------------------------------------------------------------------------
for report in filtered:
    rid = report["id"]
    (c_check, c_name, c_uav, c_time,
     c_safe, c_height, c_sens, c_status) = st.columns(COL_WEIGHTS)

    checked = c_check.checkbox(
        "select",
        value=st.session_state.selected.get(rid, False),
        key=f"chk_{rid}",
        label_visibility="collapsed",
    )
    st.session_state.selected[rid] = checked

    if c_name.button(report["Filename"], key=f"btn_{rid}", use_container_width=True):
        preview_dialog(rid)

    c_uav.write(report["UAV ID"])
    c_time.write(report["Inspection Date Time"].strftime("%Y-%m-%d %H:%M:%S %Z"))
    c_safe.write(report["Safe Clearance Distance (m)"])
    c_height.write(report["Clearance Height (m)"])
    c_sens.write(report["Sensitivity"])
    c_status.markdown(status_badge_html(report["Status"]), unsafe_allow_html=True)

st.divider()

# ---------------------------------------------------------------------------
# Download selected reports (selection persists across filters)
# ---------------------------------------------------------------------------
selected_ids = [rid for rid, is_sel in st.session_state.selected.items() if is_sel]
selected_reports = [r for r in st.session_state.reports if r["id"] in selected_ids]

if selected_reports:
    names = ", ".join(r["Filename"] for r in selected_reports)
    st.write(f"**{len(selected_reports)} file(s) selected:** {names}")

    if len(selected_reports) == 1:
        r = selected_reports[0]
        st.download_button(
            label=f"Download {r['Filename']}",
            data=r["html_bytes"],
            file_name=r["Filename"],
            mime="text/html",
        )
    else:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for r in selected_reports:
                zf.writestr(r["Filename"], r["html_bytes"])
        buf.seek(0)
        st.download_button(
            label=f"Download {len(selected_reports)} reports as .zip",
            data=buf,
            file_name="selected_reports.zip",
            mime="application/zip",
        )
else:
    st.caption("Select one or more rows to enable download.")