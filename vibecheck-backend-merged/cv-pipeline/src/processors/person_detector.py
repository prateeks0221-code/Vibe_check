"""Real YOLOv8 person detector with ByteTrack, EMA smoothing, and path history.

Mode controlled by DETECTION_MODE env var (fast | precise | gpu).
"""

import torch
import numpy as np
from typing import Any, Dict

from processors.base import BaseProcessor
from inference_runtime import get_model, PRESET

_PATH_MAX_LEN = 30
_PATH_EXPORT_LEN = 10
_EMA_ALPHA = 0.45          # blend ratio; higher = more responsive to fast movement
_GHOST_FRAMES = 3          # keep track visible this many frames after last detection

# Real-world quality filters
_MIN_PIXEL_AREA = 1200     # ignore sub-stamp blobs (noise / far background)
_MIN_ASPECT     = 0.5      # h/w ratio — persons are taller than wide
_MAX_ASPECT     = 5.0      # cap runaway tall slivers


class PersonDetector(BaseProcessor):

    name = "person_detector"

    @property
    def required_fps(self) -> float:  # type: ignore[override]
        return PRESET["required_fps"]

    def __init__(self):
        self.model = get_model()
        self._paths: Dict[int, list] = {}
        self._ema: Dict[int, list] = {}          # smoothed [x1, y1, x2, y2]
        self._ghost: Dict[int, dict] = {}        # last known det + countdown
        self._ghost_ttl: Dict[int, int] = {}     # frames remaining

    def _smooth(self, tid: int, raw: list) -> list:
        raw_py = [int(v) for v in raw]
        if tid not in self._ema:
            self._ema[tid] = raw_py
            return raw_py
        s = self._ema[tid]
        a = _EMA_ALPHA
        smoothed = [int(a * r + (1 - a) * s[i]) for i, r in enumerate(raw_py)]
        self._ema[tid] = smoothed
        return smoothed

    def process(self, frame: np.ndarray, context: Dict[str, Any]) -> Dict[str, Any]:
        h, w = frame.shape[:2]

        results = self.model.track(
            source=frame,
            persist=True,
            classes=[0],        # person class only
            conf=PRESET["conf"],
            iou=0.35,           # stricter NMS — fewer duplicate boxes on overlapping people
            verbose=False,
            tracker="bytetrack.yaml",
            imgsz=PRESET["imgsz"],
            device="cuda:0" if torch.cuda.is_available() else "cpu",
            half=torch.cuda.is_available(),
        )

        detections = []
        active_ids: set = set()

        for result in results:
            if result.boxes is None:
                continue
            ids = result.boxes.id
            for idx, box in enumerate(result.boxes):
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                confidence = float(box.conf[0])
                track_id = int(ids[idx]) if ids is not None else None

                if track_id is not None:
                    active_ids.add(track_id)
                    sx1, sy1, sx2, sy2 = self._smooth(track_id, [x1, y1, x2, y2])
                    cx, cy = int((sx1 + sx2) // 2), int((sy1 + sy2) // 2)

                    if track_id not in self._paths:
                        self._paths[track_id] = []
                    self._paths[track_id].append([cx, cy])
                    if len(self._paths[track_id]) > _PATH_MAX_LEN:
                        self._paths[track_id] = self._paths[track_id][-_PATH_MAX_LEN:]

                    bw, bh = sx2 - sx1, sy2 - sy1
                    area = bw * bh
                    aspect = bh / max(bw, 1)
                    # Drop implausible detections (tiny blobs, horizontal slivers)
                    if area < _MIN_PIXEL_AREA or not (_MIN_ASPECT <= aspect <= _MAX_ASPECT):
                        continue

                    det = {
                        "track_id": track_id,
                        "x": sx1, "y": sy1,
                        "w": bw, "h": bh,
                        "bbox": [sx1, sy1, sx2, sy2],
                        "confidence": round(confidence, 2),
                        "label": "person",
                    }
                    self._ghost[track_id] = det
                    self._ghost_ttl[track_id] = _GHOST_FRAMES
                    detections.append(det)

        # Inject ghost detections for tracks briefly lost
        for tid in list(self._ghost_ttl):
            if tid in active_ids:
                continue
            self._ghost_ttl[tid] -= 1
            if self._ghost_ttl[tid] > 0:
                ghost = dict(self._ghost[tid])
                ghost["confidence"] = round(ghost["confidence"] * 0.8, 2)
                detections.append(ghost)
            else:
                del self._ghost[tid]
                del self._ghost_ttl[tid]
                self._ema.pop(tid, None)
                self._paths.pop(tid, None)

        # Prune stale paths
        live_ids = {d["track_id"] for d in detections if d["track_id"] is not None}
        for tid in list(self._paths):
            if tid not in live_ids:
                del self._paths[tid]

        paths = {str(tid): pts[-_PATH_EXPORT_LEN:] for tid, pts in self._paths.items()}

        return {
            "venue_id": context["venue_id"],
            "timestamp": context["timestamp"],
            "frame_w": w,
            "frame_h": h,
            "person_count": len([d for d in detections if d["track_id"] in active_ids]),
            "detections": detections,
            "paths": paths,
        }
