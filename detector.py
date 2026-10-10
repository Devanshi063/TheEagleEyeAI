"""
detector.py — YOLOv8 PPE + restricted-zone safety detection logic.

PPE detection uses a zero-shot approach on YOLOv8n (COCO classes):
  - 'person'  (class 0)
  - 'helmet'  approximated by 'baseball cap' / class 0 head bbox heuristic
  - vest      no direct COCO class → we use a colour-heuristic on the
              torso region (high-vis orange/yellow/green)

For hackathon MVP we use class 0 = person + head-crop colour check for
helmet (dark/solid colour on top of person box) and torso colour check
for vest. A real deployment would use a fine-tuned PPE YOLO model.
"""

import cv2
import numpy as np
from ultralytics import YOLO
import os, datetime, uuid

_model = None
EVIDENCE_DIR = os.path.join(os.path.dirname(__file__), "evidence_frames")
os.makedirs(EVIDENCE_DIR, exist_ok=True)


def load_model():
    global _model
    if _model is None:
        _model = YOLO("yolov8n.pt")  # auto-downloads on first run
    return _model


# ── colour helpers ────────────────────────────────────────────────────────────

def _dominant_hsv(crop: np.ndarray):
    """Return the mean HSV of a cropped region (ignoring near-black pixels)."""
    if crop is None or crop.size == 0:
        return None
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    mask = hsv[:, :, 2] > 40  # skip very dark pixels
    if mask.sum() == 0:
        return None
    return hsv[mask].mean(axis=0)


def _has_hivis_colour(crop: np.ndarray) -> bool:
    """Detect high-visibility orange, yellow, or green in a region."""
    mean = _dominant_hsv(crop)
    if mean is None:
        return False
    h, s, v = mean
    # Yellow/green hue 20-85, high saturation
    if 20 <= h <= 85 and s > 80 and v > 80:
        return True
    # Orange hue 10-20
    if 10 <= h <= 20 and s > 100 and v > 100:
        return True
    return False


def _has_helmet(head_crop: np.ndarray) -> bool:
    """
    Heuristic: helmet = head crop is dominated by a non-skin,
    relatively uniform dark/solid colour (hard-hat colour range).
    For MVP we flag 'no helmet' when the top of the head crop is
    predominantly skin-tone (hue 0-20, low saturation).
    """
    mean = _dominant_hsv(head_crop)
    if mean is None:
        return False
    h, s, v = mean
    # Skin tone: hue ~0-22, saturation 20-170, value > 60
    is_skin = (0 <= h <= 22) and (20 <= s <= 170) and (v > 60)
    return not is_skin  # if NOT skin → something covering the head


# ── restricted zone check ─────────────────────────────────────────────────────

def point_in_rect(cx: int, cy: int, zone: dict) -> bool:
    """zone = {x1, y1, x2, y2} in pixel coords."""
    return zone["x1"] <= cx <= zone["x2"] and zone["y1"] <= cy <= zone["y2"]


# ── main detection function ───────────────────────────────────────────────────

def detect_frame(
    frame: np.ndarray,
    camera: str = "CAM-01",
    zone: dict | None = None,
    zone_name: str = "Zone-A",
    conf_thresh: float = 0.35,
) -> dict:
    """
    Run YOLO on a single BGR frame. Returns:
      {
        "annotated_frame": np.ndarray,
        "violations": [{"type", "confidence", "zone", "bbox"}],
        "persons_detected": int,
      }
    """
    model = load_model()
    results = model(frame, conf=conf_thresh, verbose=False)[0]

    h, w = frame.shape[:2]
    annotated = frame.copy()
    violations = []

    # Draw restricted zone
    if zone:
        cv2.rectangle(
            annotated,
            (zone["x1"], zone["y1"]),
            (zone["x2"], zone["y2"]),
            (0, 0, 220),
            2,
        )
        cv2.putText(
            annotated,
            f"RESTRICTED: {zone_name}",
            (zone["x1"] + 4, zone["y1"] + 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 220),
            2,
        )

    persons = []
    for box in results.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        name = model.names[cls_id]
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        if name == "person":
            persons.append({"bbox": (x1, y1, x2, y2), "conf": conf})

    for p in persons:
        x1, y1, x2, y2 = p["bbox"]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        box_h = y2 - y1
        box_w = x2 - x1

        # Draw person box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 200), 2)

        # ── helmet check ──────────────────────────────────────────────────────
        head_y2 = y1 + int(box_h * 0.22)
        head_crop = frame[max(0, y1): max(0, head_y2), max(0, x1): max(0, x2)]
        helmet_ok = _has_helmet(head_crop) if head_crop.size > 0 else False

        if not helmet_ok:
            violations.append(
                {
                    "type": "No Helmet",
                    "confidence": round(p["conf"], 2),
                    "zone": zone_name if zone and point_in_rect(cx, cy, zone) else "General",
                    "bbox": (x1, y1, x2, y2),
                }
            )
            cv2.putText(
                annotated,
                "NO HELMET",
                (x1, y1 - 22),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
            )

        # ── vest check ────────────────────────────────────────────────────────
        vest_y1 = y1 + int(box_h * 0.22)
        vest_y2 = y1 + int(box_h * 0.60)
        vest_crop = frame[
            max(0, vest_y1): max(0, vest_y2),
            max(0, x1 + int(box_w * 0.1)): max(0, x2 - int(box_w * 0.1)),
        ]
        vest_ok = _has_hivis_colour(vest_crop) if vest_crop.size > 0 else False

        if not vest_ok:
            violations.append(
                {
                    "type": "No Safety Vest",
                    "confidence": round(p["conf"], 2),
                    "zone": zone_name if zone and point_in_rect(cx, cy, zone) else "General",
                    "bbox": (x1, y1, x2, y2),
                }
            )
            cv2.putText(
                annotated,
                "NO VEST",
                (x1, y1 - 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 165, 255),
                2,
            )

        # ── restricted zone check ─────────────────────────────────────────────
        if zone and point_in_rect(cx, cy, zone):
            violations.append(
                {
                    "type": "Restricted Zone Intrusion",
                    "confidence": round(p["conf"], 2),
                    "zone": zone_name,
                    "bbox": (x1, y1, x2, y2),
                }
            )
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 3)
            cv2.putText(
                annotated,
                "ZONE BREACH",
                (x1, y2 + 18),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
            )

    # Overlay HUD
    cv2.putText(
        annotated,
        f"EagleEye AI | {camera}",
        (10, 22),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 230, 230),
        2,
    )
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(
        annotated,
        ts,
        (10, 44),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (180, 180, 180),
        1,
    )

    return {
        "annotated_frame": annotated,
        "violations": violations,
        "persons_detected": len(persons),
    }


def save_evidence(frame: np.ndarray) -> str:
    """Save a frame as evidence and return the relative filename."""
    fname = f"ev_{uuid.uuid4().hex[:8]}.jpg"
    path = os.path.join(EVIDENCE_DIR, fname)
    cv2.imwrite(path, frame)
    return fname
