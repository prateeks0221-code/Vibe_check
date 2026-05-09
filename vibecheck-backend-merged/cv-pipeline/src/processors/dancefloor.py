"""Dance floor activity via optical flow on a designated zone."""
import numpy as np
import cv2
from typing import Any, Dict
from processors.base import BaseProcessor


class DanceFloorProcessor(BaseProcessor):
    """
    Dummy dance-floor energy detector.
    Production swap: dense optical flow + pose estimation keypoint velocity
    calibrated against venue-specific baselines.
    """

    name = "dancefloor"
    required_fps = 2.0  # 30s refresh cadence

    def __init__(self):
        self.prev_gray = None

    def process(self, frame: np.ndarray, context: Dict[str, Any]) -> Dict[str, Any]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        energy = 0.0
        if self.prev_gray is not None:
            flow = cv2.calcOpticalFlowFarneback(
                self.prev_gray, gray, None,
                pyr_scale=0.5, levels=3, winsize=15,
                iterations=3, poly_n=5, poly_sigma=1.2, flags=0
            )
            mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            energy = float(np.mean(mag))

        self.prev_gray = gray

        # Dummy mapping to 0-100
        score = min(100, int(energy * 50))
        if score < 15:
            state = "Dead"
        elif score < 40:
            state = "Warming Up"
        elif score < 70:
            state = "Active"
        else:
            state = "Raging"

        return {
            "energy_score": score,
            "state": state,
            "timestamp": context.get("timestamp"),
            "venue_id": context.get("venue_id"),
            "zone": context.get("zone", "dancefloor"),
        }
