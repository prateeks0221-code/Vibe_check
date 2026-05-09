# """Occupancy: count heads relative to venue capacity."""
# import os
# import numpy as np
# import cv2
# from datetime import datetime
# from typing import Any, Dict
# from processors.base import BaseProcessor


# class OccupancyProcessor(BaseProcessor):
#     """
#     Dummy person detector.
#     Production swap: YOLOv8-nano or MediaPipe object detector (person class).
#     """

#     name = "occupancy"
#     required_fps = 1.0  # 1 fps is plenty for a 60s rolling window

#     def __init__(self):
#         # Dummy: use HOG + SVM OpenCV people detector as placeholder
#         self.hog = cv2.HOGDescriptor()
#         self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

#     def process(self, frame: np.ndarray, context: Dict[str, Any]) -> Dict[str, Any]:
#         if os.getenv("DUMMY_MODE", "false").lower() == "true":
#             # Generate plausible synthetic occupancy
#             import random
#             hour = datetime.fromtimestamp(context.get("timestamp", 0)).hour
#             base = 40 if 20 <= hour <= 23 else 15 if 12 <= hour <= 18 else 5
#             head_count = random.randint(base, base + 60)
#         else:
#             # Resize for speed
#             small = cv2.resize(frame, (640, 360))
#             rects, _ = self.hog.detectMultiScale(small, winStride=(8, 8), padding=(4, 4), scale=1.05)
#             head_count = len(rects)
#         return {
#             "head_count": head_count,
#             "timestamp": context.get("timestamp"),
#             "venue_id": context.get("venue_id"),
#         }
"""Real occupancy analytics."""

from typing import Dict, Any

from processors.base import BaseProcessor


class OccupancyProcessor(BaseProcessor):

    name = "occupancy"

    required_fps = 1.0

    def process(
        self,
        frame,
        context: Dict[str, Any]
    ):

        detections = context.get(
            "detections",
            []
        )

        people = [
            d for d in detections
            if d["label"] == "person"
        ]

        count = len(people)

        return {

            "venue_id": context["venue_id"],

            "timestamp": context["timestamp"],

            "head_count": count,

            "tracks": people,

            "stats": {

                "people_detected": count,

                "active_tracks": count,

                "occupancy_score": min(
                    count * 5,
                    100
                )
            }
        }