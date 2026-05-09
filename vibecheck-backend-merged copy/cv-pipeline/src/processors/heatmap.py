"""Spatial density heatmap accumulator."""
import time
import numpy as np
from typing import Any, Dict
from processors.base import BaseProcessor

GRID_W = 32
GRID_H = 18


class HeatmapProcessor(BaseProcessor):
    name = "heatmap"
    required_fps = 1.0

    def __init__(self, decay: float = 0.95):
        self.grid = np.zeros((GRID_H, GRID_W), dtype=np.float32)
        self.decay = decay
        self.total_samples = 0

    def process(self, frame: np.ndarray, context: Dict[str, Any]) -> Dict[str, Any]:
        self.grid *= self.decay
        self.total_samples += 1

        detections = context.get("detections", [])
        fh, fw = frame.shape[:2]
        cell_w = fw / GRID_W
        cell_h = fh / GRID_H

        for d in detections:
            cx = d["x"] + d["w"] // 2
            cy = d["y"] + d["h"] // 2
            gx = min(int(cx / cell_w), GRID_W - 1)
            gy = min(int(cy / cell_h), GRID_H - 1)
            self.grid[gy, gx] += 1.0

        mx = float(self.grid.max()) if self.grid.max() > 0 else 1.0
        normalised = (self.grid / mx * 100).astype(int).tolist()

        hotspots = []
        for gy in range(GRID_H):
            for gx in range(GRID_W):
                if self.grid[gy, gx] / mx > 0.7:
                    hotspots.append({
                        "grid_x": gx, "grid_y": gy,
                        "intensity": round(float(self.grid[gy, gx] / mx), 2),
                    })

        return {
            "grid": normalised,
            "grid_w": GRID_W,
            "grid_h": GRID_H,
            "hotspot_count": len(hotspots),
            "hotspots": hotspots[:10],
            "total_samples": self.total_samples,
            "timestamp": context.get("timestamp"),
            "venue_id": context.get("venue_id"),
        }
