"""
app.py — Streamlit frontend for TheEagleEye AI
Branded: dark navy + cyan + purple | CompileTheCode
"""

import base64, io, os, time, datetime
import requests
import streamlit as st
from PIL import Image

API = "http://localhost:8000"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TheEagleEye AI | CompileTheCode",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS — dark navy + cyan + purple ────────────────────────────────────
st.markdown(
    """
<style>
/* ── base ── */
html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
}
.stApp {
    background: #0a0f1e;
    color: #e0e8f0;
}

/* ── sidebar ── */
[data-testid="stSidebar"] {
    background: #0d1528 !important;
    border-right: 1px solid #1e3a5f;
}
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #00e5ff;
}
[data-testid="stSidebarNav"] {
    background: transparent;
}

/* ── metric cards ── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #0d1a33, #0f2040);
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 12px 16px;
}
[data-testid="metric-container"] label {
    color: #8ab4d4 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #00e5ff !important;
    font-size: 2rem !important;
    font-weight: 700;
}

/* ── section headers ── */
.eagle-header {
    background: linear-gradient(90deg, #00e5ff22, #7c3aed22, transparent);
    border-left: 4px solid #00e5ff;
    padding: 10px 18px;
    border-radius: 6px;
    margin: 18px 0 10px 0;
}
.eagle-header h2 {
    color: #00e5ff;
    margin: 0;
    font-size: 1.25rem;
    letter-spacing: 0.04em;
}

/* ── violation badge ── */
.badge-open      { background:#dc2626; color:#fff; padding:2px 10px; border-radius:12px; font-size:0.78rem; font-weight:600; }
.badge-ack       { background:#7c3aed; color:#fff; padding:2px 10px; border-radius:12px; font-size:0.78rem; font-weight:600; }
.badge-escalated { background:#f59e0b; color:#000; padding:2px 10px; border-radius:12px; font-size:0.78rem; font-weight:600; }

/* ── alert box ── */
.alert-box {
    background: #1a0f2e;
    border: 1px solid #7c3aed;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 10px 0;
    color: #c4b5fd;
    font-size: 0.9rem;
}
.alert-box.danger {
    background: #1a0f0f;
    border-color: #dc2626;
    color: #fca5a5;
}
.alert-box.success {
    background: #0f1a12;
    border-color: #16a34a;
    color: #86efac;
}

/* ── incident table row ── */
.inc-row {
    background: #0d1528;
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 6px 0;
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
}

/* ── camera card ── */
.cam-card {
    background: linear-gradient(135deg, #0d1a33, #111e3a);
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    margin: 6px 0;
}
.cam-card .dot-online  { color: #22c55e; font-size: 1.3rem; }
.cam-card .dot-offline { color: #dc2626; font-size: 1.3rem; }
.cam-card h4 { color: #00e5ff; margin: 4px 0 2px 0; font-size: 0.95rem; }
.cam-card p  { color: #8ab4d4; font-size: 0.78rem; margin: 0; }

/* ── branding ── */
.brand-title {
    background: linear-gradient(90deg, #00e5ff, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 1.7rem;
    font-weight: 800;
    letter-spacing: 0.03em;
}
.brand-sub {
    color: #8ab4d4;
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

/* ── buttons ── */
.stButton > button {
    background: linear-gradient(90deg, #00e5ff33, #7c3aed33) !important;
    border: 1px solid #00e5ff66 !important;
    color: #00e5ff !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #00e5ff55, #7c3aed55) !important;
    border-color: #00e5ff !important;
}

/* ── file uploader ── */
[data-testid="stFileUploader"] {
    background: #0d1528;
    border: 1px dashed #1e3a5f;
    border-radius: 8px;
}

/* ── select / input ── */
.stSelectbox > div > div, .stTextInput > div > div > input {
    background: #0d1528 !important;
    border-color: #1e3a5f !important;
    color: #e0e8f0 !important;
}

/* scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0f1e; }
::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 3px; }
</style>
""",
    unsafe_allow_html=True,
)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div class="brand-title">🦅 EagleEye AI</div>'
        '<div class="brand-sub">CompileTheCode | Industrial Safety</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "🔍 Analyze Media", "🚨 Incident Center"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("### ⚙️ Detection Config")
    camera_id = st.selectbox("Camera ID", ["CAM-01", "CAM-02", "CAM-03", "CAM-04"])
    zone_name = st.text_input("Zone Name", value="Zone-A")
    st.markdown("**Restricted Zone (pixels)**")
    z_col1, z_col2 = st.columns(2)
    zone_x1 = z_col1.number_input("X1", value=0, step=10)
    zone_y1 = z_col2.number_input("Y1", value=0, step=10)
    zone_x2 = z_col1.number_input("X2", value=200, step=10)
    zone_y2 = z_col2.number_input("Y2", value=200, step=10)
    st.markdown("---")
    st.markdown(
        '<div style="color:#4a6fa5;font-size:0.72rem;text-align:center;">'
        "v1.0 · Hackathon MVP · 2026</div>",
        unsafe_allow_html=True,
    )


# ── helper: fetch stats ───────────────────────────────────────────────────────

def fetch_stats():
    try:
        r = requests.get(f"{API}/stats", timeout=4)
        return r.json()
    except Exception:
        return {
            "total_incidents": "—",
            "open": "—",
            "acknowledged": "—",
            "escalated": "—",
            "active_cameras": "—",
            "ai_status": "Offline",
        }


def fetch_incidents(status=None):
    try:
        params = {"status": status} if status else {}
        r = requests.get(f"{API}/incidents", params=params, timeout=4)
        return r.json()
    except Exception:
        return []


def update_incident(inc_id, new_status):
    try:
        requests.put(f"{API}/incidents/{inc_id}", json={"status": new_status}, timeout=4)
    except Exception:
        pass


def section(title: str):
    st.markdown(
        f'<div class="eagle-header"><h2>{title}</h2></div>', unsafe_allow_html=True
    )


# ── PAGE: DASHBOARD ───────────────────────────────────────────────────────────
if page == "📊 Dashboard":
    st.markdown(
        '<div class="brand-title" style="font-size:2.2rem;">🦅 TheEagleEye AI</div>'
        '<div class="brand-sub" style="margin-bottom:18px;">Industrial Safety Intelligence Platform · CompileTheCode</div>',
        unsafe_allow_html=True,
    )

    stats = fetch_stats()
    ai_color = "#22c55e" if stats["ai_status"] == "Online" else "#dc2626"

    # ── KPI row ──────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🎥 Active Cameras", stats["active_cameras"])
    c2.metric("🚨 Open Alerts", stats["open"])
    c3.metric("✅ Acknowledged", stats["acknowledged"])
    c4.metric("⚡ Escalated", stats["escalated"])
    c5.metric("📋 Total Incidents", stats["total_incidents"])

    st.markdown(
        f'<div style="text-align:right;margin-top:-10px;">'
        f'<span style="color:{ai_color};font-size:0.85rem;font-weight:600;">'
        f'● AI Engine: {stats["ai_status"]}</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Camera Grid ──────────────────────────────────────────────────────────
    section("🎥 Active Camera Feeds")
    cam_cols = st.columns(4)
    cameras = [
        ("CAM-01", "Main Gate", True),
        ("CAM-02", "Assembly Floor", True),
        ("CAM-03", "Warehouse", True),
        ("CAM-04", "Chemical Zone", False),
    ]
    for col, (cid, location, online) in zip(cam_cols, cameras):
        dot = "dot-online" if online else "dot-offline"
        status_text = "● LIVE" if online else "● OFFLINE"
        col.markdown(
            f'<div class="cam-card">'
            f'<div class="{dot}">{status_text}</div>'
            f"<h4>{cid}</h4>"
            f"<p>{location}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Recent incidents ──────────────────────────────────────────────────────
    section("🚨 Recent Safety Events")
    incidents = fetch_incidents()[:10]
    if not incidents:
        st.info("No incidents recorded yet. Upload media in **Analyze Media** to begin.")
    else:
        for inc in incidents:
            badge_cls = {
                "Open": "badge-open",
                "Acknowledged": "badge-ack",
                "Escalated": "badge-escalated",
            }.get(inc["status"], "badge-open")

            evidence_url = f"{API}/evidence/{inc['evidence']}" if inc.get("evidence") else None

            with st.container():
                col_info, col_ev = st.columns([3, 1])
                with col_info:
                    st.markdown(
                        f'<div class="inc-row">'
                        f'<span class="{badge_cls}">{inc["status"]}</span>'
                        f'<span style="color:#00e5ff;font-weight:600;">{inc["violation"]}</span>'
                        f'<span style="color:#8ab4d4;font-size:0.82rem;">'
                        f'📷 {inc["camera"]} &nbsp;|&nbsp; 📍 {inc["zone"]} &nbsp;|&nbsp; '
                        f'🕒 {inc["timestamp"]} &nbsp;|&nbsp; '
                        f'🎯 Conf: {inc["confidence"]:.0%}'
                        f"</span></div>",
                        unsafe_allow_html=True,
                    )
                with col_ev:
                    if evidence_url:
                        try:
                            img_resp = requests.get(evidence_url, timeout=3)
                            st.image(img_resp.content, width=130, caption="Evidence")
                        except Exception:
                            st.caption("Evidence unavailable")

    st.markdown("---")

    # ── AI Status Panel ──────────────────────────────────────────────────────
    section("🤖 AI Engine Status")
    s1, s2, s3 = st.columns(3)
    s1.markdown(
        '<div class="cam-card"><h4>YOLOv8n</h4><p style="color:#22c55e;">● Model Loaded</p></div>',
        unsafe_allow_html=True,
    )
    s2.markdown(
        '<div class="cam-card"><h4>PPE Detector</h4><p style="color:#22c55e;">● Active</p></div>',
        unsafe_allow_html=True,
    )
    s3.markdown(
        '<div class="cam-card"><h4>Zone Monitor</h4><p style="color:#22c55e;">● Active</p></div>',
        unsafe_allow_html=True,
    )


# ── PAGE: ANALYZE MEDIA ───────────────────────────────────────────────────────
elif page == "🔍 Analyze Media":
    st.markdown(
        '<div class="brand-title">🔍 Analyze Media</div>'
        '<div class="brand-sub" style="margin-bottom:18px;">Upload Image or Video · YOLO PPE + Zone Detection</div>',
        unsafe_allow_html=True,
    )

    # Zone preview
    with st.expander("📐 Restricted Zone Preview", expanded=False):
        st.info(
            f"Restricted zone set to: X1={zone_x1}, Y1={zone_y1}, X2={zone_x2}, Y2={zone_y2}  "
            f"on **{zone_name}**. Adjust in the sidebar."
        )
        if zone_x2 > zone_x1 and zone_y2 > zone_y1:
            import numpy as np
            import cv2
            preview = np.zeros((max(zone_y2 + 20, 240), max(zone_x2 + 20, 320), 3), dtype=np.uint8)
            preview[:] = (13, 21, 40)
            cv2.rectangle(preview, (zone_x1, zone_y1), (zone_x2, zone_y2), (0, 0, 220), 2)
            cv2.putText(preview, f"RESTRICTED: {zone_name}", (zone_x1 + 4, zone_y1 + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 220), 1)
            from PIL import Image as PILImage
            st.image(PILImage.fromarray(cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)),
                     caption="Zone Preview", use_container_width=False, width=400)

    uploaded = st.file_uploader(
        "Upload an Image or Video",
        type=["jpg", "jpeg", "png", "bmp", "mp4", "avi", "mov"],
    )

    if uploaded:
        suffix = os.path.splitext(uploaded.name)[1].lower() if hasattr(uploaded, 'name') else ""
        is_video = suffix in {".mp4", ".avi", ".mov", ".mkv"}

        if not is_video:
            st.image(uploaded, caption="Uploaded Image", use_container_width=True)

        run = st.button("🚀 Run EagleEye Detection")

        if run:
            with st.spinner("🦅 EagleEye AI is scanning for violations..."):
                files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
                data = {
                    "camera": camera_id,
                    "zone_name": zone_name,
                    "zone_x1": int(zone_x1),
                    "zone_y1": int(zone_y1),
                    "zone_x2": int(zone_x2),
                    "zone_y2": int(zone_y2),
                }
                try:
                    resp = requests.post(f"{API}/analyze", files=files, data=data, timeout=120)
                    result = resp.json()
                except Exception as e:
                    st.error(f"Backend error: {e}")
                    st.stop()

            # Alert banner
            alert = result.get("alert_message", "")
            if "violation" in alert.lower() and "0" not in alert[:15]:
                st.markdown(
                    f'<div class="alert-box danger">🚨 {alert}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="alert-box success">{alert}</div>',
                    unsafe_allow_html=True,
                )

            # Annotated image
            if result.get("annotated_image"):
                img_data = base64.b64decode(result["annotated_image"])
                st.image(img_data, caption="EagleEye Detection Output", use_container_width=True)

            # Violation list
            violations = result.get("violations", [])
            if violations:
                section("⚠️ Violations Detected")
                for v in violations:
                    badge = (
                        "badge-open"
                        if "Zone" in v["type"]
                        else "badge-escalated"
                    )
                    st.markdown(
                        f'<div class="inc-row">'
                        f'<span class="{badge}">VIOLATION</span>'
                        f'<span style="color:#00e5ff;font-weight:600;">{v["type"]}</span>'
                        f'<span style="color:#8ab4d4;font-size:0.82rem;">'
                        f'📷 {v.get("camera",camera_id)} &nbsp;|&nbsp; '
                        f'📍 {v["zone"]} &nbsp;|&nbsp; '
                        f'🎯 Conf: {v["confidence"]:.0%}'
                        f"</span></div>",
                        unsafe_allow_html=True,
                    )
                st.markdown(
                    '<div class="alert-box">'
                    "📧 <strong>Simulated Alert:</strong> Email & SMS notification dispatched "
                    "to <em>hr@company.com</em> and <em>safety.officer@company.com</em>"
                    "</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.success("✅ No PPE violations or zone breaches detected.")


# ── PAGE: INCIDENT CENTER ─────────────────────────────────────────────────────
elif page == "🚨 Incident Center":
    import os  # noqa: F811
    st.markdown(
        '<div class="brand-title">🚨 Incident Center</div>'
        '<div class="brand-sub" style="margin-bottom:18px;">Manage Safety Incidents · Open / Acknowledged / Escalated</div>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["🔴 Open", "🟣 Acknowledged", "🟡 Escalated"])

    def render_incidents(status: str):
        incidents = fetch_incidents(status)
        if not incidents:
            st.info(f"No {status} incidents.")
            return
        for inc in incidents:
            with st.container():
                c1, c2, c3 = st.columns([4, 1, 1])
                with c1:
                    badge_cls = {
                        "Open": "badge-open",
                        "Acknowledged": "badge-ack",
                        "Escalated": "badge-escalated",
                    }.get(inc["status"], "badge-open")
                    st.markdown(
                        f'<div class="inc-row">'
                        f'<span class="{badge_cls}">{inc["status"]}</span>'
                        f'<b style="color:#00e5ff;">#{inc["id"]} — {inc["violation"]}</b><br/>'
                        f'<span style="color:#8ab4d4;font-size:0.82rem;">'
                        f'📷 {inc["camera"]} &nbsp;|&nbsp; 📍 {inc["zone"]} &nbsp;|&nbsp; '
                        f'🕒 {inc["timestamp"]} &nbsp;|&nbsp; '
                        f'🎯 {inc["confidence"]:.0%}'
                        f"</span></div>",
                        unsafe_allow_html=True,
                    )
                with c2:
                    evidence_url = (
                        f"{API}/evidence/{inc['evidence']}" if inc.get("evidence") else None
                    )
                    if evidence_url:
                        try:
                            img_resp = requests.get(evidence_url, timeout=3)
                            st.image(img_resp.content, width=110, caption="Evidence")
                        except Exception:
                            st.caption("N/A")
                with c3:
                    new_status = st.selectbox(
                        "Status",
                        ["Open", "Acknowledged", "Escalated"],
                        index=["Open", "Acknowledged", "Escalated"].index(inc["status"]),
                        key=f"sel_{inc['id']}",
                        label_visibility="collapsed",
                    )
                    if st.button("Update", key=f"upd_{inc['id']}"):
                        update_incident(inc["id"], new_status)
                        st.toast(f"Incident #{inc['id']} → {new_status}", icon="✅")
                        time.sleep(0.4)
                        st.rerun()

                # Alert sent chip
                if inc.get("alert_sent"):
                    st.markdown(
                        '<div style="margin-left:8px;margin-top:-4px;">'
                        '<span style="background:#7c3aed22;border:1px solid #7c3aed;'
                        'color:#c4b5fd;padding:2px 10px;border-radius:12px;font-size:0.72rem;">'
                        "📧 Alert sent to HR/Safety Officer</span></div>",
                        unsafe_allow_html=True,
                    )
            st.markdown("<hr style='border-color:#1e3a5f;margin:4px 0;'>", unsafe_allow_html=True)

    with tab1:
        render_incidents("Open")
    with tab2:
        render_incidents("Acknowledged")
    with tab3:
        render_incidents("Escalated")

    st.markdown("---")
    section("📊 Incident Statistics")
    stats = fetch_stats()
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Total", stats["total_incidents"])
    sc2.metric("Open", stats["open"])
    sc3.metric("Acknowledged", stats["acknowledged"])
    sc4.metric("Escalated", stats["escalated"])
