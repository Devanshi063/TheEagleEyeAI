# 🦅 TheEagleEye AI — Industrial Safety Intelligence
> **CompileTheCode Hackathon MVP**

---

## 📁 Folder Structure

```
EagleEyeAI/
├── backend/
│   ├── main.py              ← FastAPI backend (all API routes)
│   ├── detector.py          ← YOLOv8 PPE + zone detection logic
│   ├── database.py          ← SQLite setup & helpers
│   ├── evidence_frames/     ← Auto-saved violation screenshots
│   └── eagleeye.db          ← SQLite database (auto-created)
├── frontend/
│   └── app.py               ← Streamlit dashboard
├── models/                  ← (yolov8n.pt auto-downloads here on first run)
└── requirements.txt
```

---

## ⚡ Quick Start (VS Code Terminal)

### 1. Create & activate a virtual environment

```powershell
cd c:\Users\Dell\Desh\EagleEyeAI
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Start the FastAPI backend (Terminal 1)

```powershell
cd backend
uvicorn main:app --reload --port 8000
```

> First run will auto-download `yolov8n.pt` (~6 MB).

### 4. Start the Streamlit frontend (Terminal 2)

```powershell
cd frontend
streamlit run app.py --server.port 8501
```

Open **http://localhost:8501** in your browser.

---

## 🔄 Core Flow

```
Upload Image/Video
    ↓
FastAPI /analyze endpoint
    ↓
YOLOv8n person detection
    ↓
PPE heuristic (head colour → helmet, torso colour → vest)
    ↓
Restricted zone intersection check
    ↓
Violations → Evidence frame saved as JPEG
    ↓
Incident logged to SQLite (status: Open, alert_sent: 1)
    ↓
"Alert sent to HR/Safety Officer" notification displayed
    ↓
Dashboard / Incident Center shows results
```

---

## ✨ Features

| # | Feature |
|---|---------|
| 1 | Dashboard: active cameras, open alerts, AI status |
| 2 | Upload image/video → YOLO inference |
| 3 | Detect person + helmet/vest PPE violations |
| 4 | Configurable rectangular restricted zone |
| 5 | Evidence screenshot saved on violation |
| 6 | Violation type, timestamp, camera, zone, evidence shown |
| 7 | Incident Center: Open / Acknowledged / Escalated |
| 8 | Simulated "Alert sent to HR/Safety Officer" |
| 9 | SQLite incident persistence |
| 10 | Dark navy + cyan + purple branded UI |

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analyze` | Upload media, run YOLO |
| `GET` | `/incidents` | All incidents (optional `?status=Open`) |
| `PUT` | `/incidents/{id}` | Update incident status |
| `GET` | `/stats` | Dashboard KPIs |
| `GET` | `/evidence/{file}` | Serve evidence image |

---

## ⚠️ PPE Detection Note

The MVP uses **YOLOv8n (COCO)** with colour heuristics:
- **Helmet**: top 22% of person bounding box — if NOT skin-tone → helmet present
- **Vest**: torso region (22–60% of box) — if high-vis yellow/orange/green → vest present

For production, replace with a fine-tuned PPE-specific YOLO model.

---

*Built with ❤️ by CompileTheCode for the Industrial Safety Hackathon.*
