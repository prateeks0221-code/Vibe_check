"""Occupancy: count heads relative to venue capacity."""
import numpy as np
import cv2
import logging
from typing import Any, Dict
from processors.base import BaseProcessor
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class OccupancyProcessor(BaseProcessor):
    """
    YOLOv8 person detector.
    """

    name = "occupancy"
    required_fps = 1.0  # 1 fps is plenty for a 60s rolling window

    def __init__(self):
        # Load the YOLOv8-nano model (downloads automatically if missing)
        logger.info("Loading YOLOv8 model for occupancy...")
        self.model = YOLO("yolov8n.pt")
        # Class 0 is 'person' in COCO dataset
        self.classes = [0]

    def process(self, frame: np.ndarray, context: Dict[str, Any]) -> Dict[str, Any]:
        # Run inference (verbose=False to avoid console spam)
        results = self.model(frame, classes=self.classes, verbose=False)
        
        # Count bounding boxes
        head_count = len(results[0].boxes)
        
        return {
            "head_count": head_count,
            "timestamp": context.get("timestamp"),
            "venue_id": context.get("venue_id"),
        }
