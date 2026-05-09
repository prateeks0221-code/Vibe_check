"""Person detection with bounding boxes, tracking IDs, and confidence scores."""
import os
import time
import math
import numpy as np
import cv2
from typing import Any, Dict, List
from processors.base import BaseProcessor

DUMMY_MODE = os.getenv("DUMMY_MODE", "true").lower() == "true"


class SimpleCentroidTracker:
    """Centroid-based tracker: match detections to existing tracks by distance."""

    def __init__(self, max_disappeared: int = 15):
        self.next_id = 1
        self.objects = {}  # id -> centroid
        self.disappeared = {}
        self.max_disappeared = max_disappeared
        self.paths = {}  # id -> list of recent centroids

    def update(self, detections: List[dict]) -> List[dict]:
        centroids = []
        for d in detections:
            cx = d["x"] + d["w"] // 2
            cy = d["y"] + d["h"] // 2
            centroids.append((cx, cy, d))

        if not centroids:
            for oid in list(self.disappeared):
                self.disappeared[oid] += 1
                if self.disappeared[oid] > self.max_disappeared:
                    del self.objects[oid]
                    del self.disappeared[oid]
                    self.paths.pop(oid, None)
            return []

        if not self.objects:
            for cx, cy, d in centroids:
                self._register(cx, cy, d)
            return detections

        obj_ids = list(self.objects.keys())
        obj_cents = list(self.objects.values())

        dists = np.zeros((len(obj_cents), len(centroids)))
        for i, oc in enumerate(obj_cents):
            for j, (cx, cy, _) in enumerate(centroids):
                dists[i, j] = math.hypot(oc[0] - cx, oc[1] - cy)

        used_rows = set()
        used_cols = set()
        matched = []

        flat = np.argsort(dists, axis=None)
        for idx in flat:
            r, c = divmod(int(idx), len(centroids))
            if r in used_rows or c in used_cols:
                continue
            if dists[r, c] > 120:
                break
            matched.append((r, c))
            used_rows.add(r)
            used_cols.add(c)

        for r, c in matched:
            oid = obj_ids[r]
            cx, cy, d = centroids[c]
            self.objects[oid] = (cx, cy)
            self.disappeared[oid] = 0
            d["track_id"] = oid
            if oid not in self.paths:
                self.paths[oid] = []
            self.paths[oid].append((cx, cy))
            if len(self.paths[oid]) > 30:
                self.paths[oid] = self.paths[oid][-30:]

        for c in range(len(centroids)):
            if c not in used_cols:
                cx, cy, d = centroids[c]
                self._register(cx, cy, d)

        for r in range(len(obj_ids)):
            if r not in used_rows:
                oid = obj_ids[r]
                self.disappeared[oid] += 1
                if self.disappeared[oid] > self.max_disappeared:
                    del self.objects[oid]
                    del self.disappeared[oid]
                    self.paths.pop(oid, None)

        return detections

    def _register(self, cx, cy, d):
        self.objects[self.next_id] = (cx, cy)
        self.disappeared[self.next_id] = 0
        self.paths[self.next_id] = [(cx, cy)]
        d["track_id"] = self.next_id
        self.next_id += 1


class PersonDetector(BaseProcessor):
    name = "person_detector"
    required_fps = 5.0

    def __init__(self):
        self.tracker = SimpleCentroidTracker(max_disappeared=15)
        self._model = None
        if not DUMMY_MODE:
            from inference_runtime import get_model
            self._model = get_model("yolov8n")

    def process(self, frame: np.ndarray, context: Dict[str, Any]) -> Dict[str, Any]:
        h, w = frame.shape[:2]
        ts = context.get("timestamp", time.time())

        if DUMMY_MODE:
            detections = self._dummy_detect(w, h, ts)
        else:
            detections = self._yolo_detect(frame)

        tracked = self.tracker.update(detections)

        paths = {}
        for d in tracked:
            tid = d.get("track_id")
            if tid and tid in self.tracker.paths:
                paths[str(tid)] = self.tracker.paths[tid][-10:]

        return {
            "detections": tracked,
            "person_count": len(tracked),
            "paths": paths,
            "frame_w": w,
            "frame_h": h,
            "timestamp": ts,
            "venue_id": context.get("venue_id"),
        }

    def _dummy_detect(self, w, h, ts):
        detections = []
        n_people = 8 + int(5 * np.sin(ts * 0.1))
        for i in range(max(3, n_people)):
            cx = int((w * 0.15) + (w * 0.7) * ((np.sin(ts * 0.3 + i * 1.7) + 1) / 2))
            cy = int((h * 0.2) + (h * 0.6) * ((np.cos(ts * 0.2 + i * 2.3) + 1) / 2))
            bw = int(40 + 20 * np.sin(ts + i))
            bh = int(80 + 30 * np.cos(ts * 0.5 + i))
            conf = round(0.65 + 0.3 * abs(np.sin(ts * 0.4 + i)), 2)
            detections.append({
                "x": max(0, cx - bw // 2),
                "y": max(0, cy - bh // 2),
                "w": bw,
                "h": bh,
                "confidence": min(conf, 0.99),
                "class": "person",
            })
        return detections

    def _yolo_detect(self, frame):
        if not self._model:
            return []
        results = self._model(frame, classes=[0], conf=0.4, verbose=False)
        detections = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                detections.append({
                    "x": int(x1),
                    "y": int(y1),
                    "w": int(x2 - x1),
                    "h": int(y2 - y1),
                    "confidence": round(float(box.conf[0]), 2),
                    "class": "person",
                })
        return detections
