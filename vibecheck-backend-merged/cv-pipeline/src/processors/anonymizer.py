"""Privacy gate: blur faces before any frame leaves the pipeline."""
import cv2
import numpy as np
from typing import Any, Dict
from processors.base import BaseProcessor


class Anonymizer(BaseProcessor):
    """
    Dummy face anonymiser.
    In production: swap the Haar cascade for a YOLO-face / RetinaFace ONNX model
    and apply pixelation or Gaussian blur per bounding box.
    """

    name = "anonymizer"
    required_fps = 15.0  # must run on every frame going to The Mirror

    def __init__(self):
        # Haar cascade is fast and good enough for a dummy; replace with DNN in prod
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def process(self, frame: np.ndarray, context: Dict[str, Any]) -> Dict[str, Any]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        out = frame.copy()
        for (x, y, w, h) in faces:
            # heavy Gaussian blur = non-negotiable privacy filter
            roi = out[y : y + h, x : x + w]
            roi = cv2.GaussianBlur(roi, (99, 99), 30)
            out[y : y + h, x : x + w] = roi

        # Do NOT include the frame in the published payload (not JSON serializable)
        return {"face_count": len(faces)}
