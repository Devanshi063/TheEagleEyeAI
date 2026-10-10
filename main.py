"""
main.py — FastAPI backend for EagleEye AI.

Endpoints:
  POST /analyze        — upload image/video, run YOLO, store incidents
  GET  /incidents      — fetch all incidents with optional status filter
  PUT  /incidents/{id} — update incident status
  GET  /stats          — dashboard summary
  GET  /evidence/{filename} — serve evidence images
"""

import base64, datetime, io, os, shutil, tempfile
import cv2
import numpy as np
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from database import init_db, get_conn
from detector import detect_frame, save_evidence

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="EagleEye AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

EVIDENCE_DIR = os.path.join(os.path.dirname(__file__), "evidence_frames")
app.mount("/evidence", StaticFiles(directory=EVIDENCE_DIR), name="evidence")

# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    init_db()


# ── helpers ───────────────────────────────────────────────────────────────────

def _log_incident(
    camera: str,
    zone: str,
    violation: str,
    confidence: float,
    evidence_file: str | None,
):
    conn = get_conn()
    ts = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    conn.execute(
        """
        INSERT INTO incidents (timestamp, camera, zone, violation, confidence, evidence, status, alert_sent)
        VALUES (?, ?, ?, ?, ?, ?, 'Open', 1)
        """,
        (ts, camera, zone, violation, confidence, evidence_file),
    )
    conn.commit()
    conn.close()


def _parse_zone(
    zone_x1: int, zone_y1: int, zone_x2: int, zone_y2: int
) -> dict | None:
    if zone_x2 > zone_x1 and zone_y2 > zone_y1:
        return {"x1": zone_x1, "y1": zone_y1, "x2": zone_x2, "y2": zone_y2}
    return None


# ── routes ────────────────────────────────────────────────────────────────────

@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    camera: str = Form("CAM-01"),
    zone_name: str = Form("Zone-A"),
    zone_x1: int = Form(0),
    zone_y1: int = Form(0),
    zone_x2: int = Form(0),
    zone_y2: int = Form(0),
):
    """Process an uploaded image or video and return detection results."""
    suffix = os.path.splitext(file.filename)[1].lower()
    is_video = suffix in {".mp4", ".avi", ".mov", ".mkv", ".webm"}

    # Save upload to temp file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    shutil.copyfileobj(file.file, tmp)
    tmp.close()

    zone = _parse_zone(zone_x1, zone_y1, zone_x2, zone_y2)

    all_violations = []
    annotated_b64 = None

    try:
        if is_video:
            cap = cv2.VideoCapture(tmp.name)
            frame_idx = 0
            sample_every = 30  # analyse every 30th frame for MVP speed
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_idx % sample_every == 0:
                    result = detect_frame(frame, camera=camera, zone=zone, zone_name=zone_name)
                    if result["violations"]:
                        ev_fname = save_evidence(result["annotated_frame"])
                        for v in result["violations"]:
                            _log_incident(camera, v["zone"], v["type"], v["confidence"], ev_fname)
                        all_violations.extend(result["violations"])
                        if annotated_b64 is None:
                            _, buf = cv2.imencode(".jpg", result["annotated_frame"])
                            annotated_b64 = base64.b64encode(buf).decode()
                frame_idx += 1
            cap.release()
        else:
            img_bytes = open(tmp.name, "rb").read()
            arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is None:
                raise HTTPException(status_code=400, detail="Cannot decode image.")
            result = detect_frame(frame, camera=camera, zone=zone, zone_name=zone_name)
            all_violations = result["violations"]
            _, buf = cv2.imencode(".jpg", result["annotated_frame"])
            annotated_b64 = base64.b64encode(buf).decode()
            if result["violations"]:
                ev_fname = save_evidence(result["annotated_frame"])
                for v in result["violations"]:
                    _log_incident(camera, v["zone"], v["type"], v["confidence"], ev_fname)
            else:
                ev_fname = None
    finally:
        os.unlink(tmp.name)

    alert_msg = (
        f"⚠️ ALERT SENT to HR/Safety Officer — {len(all_violations)} violation(s) detected on {camera}."
        if all_violations
        else "✅ No violations detected."
    )

    return {
        "violations": [
            {k: v for k, v in viol.items() if k != "bbox"} for viol in all_violations
        ],
        "annotated_image": annotated_b64,
        "alert_message": alert_msg,
    }


@app.get("/incidents")
def get_incidents(status: str | None = None):
    conn = get_conn()
    if status:
        rows = conn.execute(
            "SELECT * FROM incidents WHERE status=? ORDER BY id DESC", (status,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM incidents ORDER BY id DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.put("/incidents/{incident_id}")
def update_incident(incident_id: int, body: dict):
    allowed = {"Open", "Acknowledged", "Escalated"}
    new_status = body.get("status", "")
    if new_status not in allowed:
        raise HTTPException(status_code=400, detail=f"Status must be one of {allowed}")
    conn = get_conn()
    conn.execute(
        "UPDATE incidents SET status=? WHERE id=?", (new_status, incident_id)
    )
    conn.commit()
    conn.close()
    return {"ok": True, "id": incident_id, "status": new_status}


@app.get("/stats")
def get_stats():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
    open_ = conn.execute("SELECT COUNT(*) FROM incidents WHERE status='Open'").fetchone()[0]
    ack = conn.execute("SELECT COUNT(*) FROM incidents WHERE status='Acknowledged'").fetchone()[0]
    esc = conn.execute("SELECT COUNT(*) FROM incidents WHERE status='Escalated'").fetchone()[0]
    conn.close()
    return {
        "total_incidents": total,
        "open": open_,
        "acknowledged": ack,
        "escalated": esc,
        "active_cameras": 4,   # simulated for MVP
        "ai_status": "Online",
    }
