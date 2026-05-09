"""YOLOv8 inference runtime with detection-mode presets."""

import os
import torch
import numpy as np
from ultralytics import YOLO

# DETECTION_MODE=fast   → yolov8n, 416px, conf 0.30, 10 fps  (rapid crowd)
# DETECTION_MODE=precise → yolov8m, 640px, conf 0.40,  5 fps  (precision count)

PRESETS = {
    "fast": {
        "default_model": "/models/yolov8n.pt",
        "imgsz": 416,
        "conf": 0.30,
        "required_fps": 10.0,
    },
    "precise": {
        "default_model": "/models/yolov8m.pt",
        "imgsz": 640,
        "conf": 0.40,
        "required_fps": 5.0,
    },
}

_DETECTION_MODE = os.getenv("DETECTION_MODE", "fast")
PRESET = PRESETS.get(_DETECTION_MODE, PRESETS["fast"])

_model = None


def get_model():
    global _model

    if _model is None:
        # MODEL_PATH overrides preset default when explicitly set
        model_path = os.getenv("MODEL_PATH", PRESET["default_model"])

        device = "cuda:0" if torch.cuda.is_available() else "cpu"

        print(f"[YOLO] mode={_DETECTION_MODE} model={model_path} device={device}")

        _model = YOLO(model_path)
        _model.to(device)

    return _model


def warmup():
    print(f"[YOLO] Warmup (imgsz={PRESET['imgsz']})...")

    model = get_model()
    dummy = np.zeros((PRESET["imgsz"], PRESET["imgsz"], 3), dtype=np.uint8)
    model.predict(source=dummy, verbose=False)

    print("[YOLO] Warmup complete")
