"""Real YOLOv8 person detector with ByteTrack and path history.

Mode controlled by DETECTION_MODE env var (fast | precise).
"""

import numpy as np
from typing import Any, Dict

from processors.base import BaseProcessor
from inference_runtime import get_model, PRESET

_PATH_MAX_LEN = 30
_PATH_EXPORT_LEN = 10


class PersonDetector(BaseProcessor):

    name = "person_detector"

    @property
    def required_fps(self) -> float:  # type: ignore[override]
        return PRESET["required_fps"]

    def __init__(self):
        self.model = get_model()
        self._paths: Dict[int, list] = {}

    def process(self, frame: np.ndarray, context: Dict[str, Any]) -> Dict[str, Any]:
        h, w = frame.shape[:2]

        results = self.model.track(
            source=frame,
            persist=True,
            classes=[0],
            conf=PRESET["conf"],
            verbose=False,
            tracker="bytetrack.yaml",
            imgsz=PRESET["imgsz"],
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
                    cx, cy = int((x1 + x2) // 2), int((y1 + y2) // 2)
                    if track_id not in self._paths:
                        self._paths[track_id] = []
                    self._paths[track_id].append([cx, cy])
                    if len(self._paths[track_id]) > _PATH_MAX_LEN:
                        self._paths[track_id] = self._paths[track_id][-_PATH_MAX_LEN:]

                detections.append({
                    "track_id": track_id,
                    "x": int(x1),
                    "y": int(y1),
                    "w": int(x2 - x1),
                    "h": int(y2 - y1),
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence": round(confidence, 2),
                    "label": "person",
                })

        # Drop paths for IDs not seen this frame
        for tid in list(self._paths):
            if tid not in active_ids:
                del self._paths[tid]

        paths = {
            str(tid): pts[-_PATH_EXPORT_LEN:]
            for tid, pts in self._paths.items()
        }

        return {
            "venue_id": context["venue_id"],
            "timestamp": context["timestamp"],
            "frame_w": w,
            "frame_h": h,
            "person_count": len(detections),
            "detections": detections,
            "paths": paths,
        }
