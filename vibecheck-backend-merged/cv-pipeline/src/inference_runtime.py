"""YOLOv8 inference runtime with detection-mode presets.

DETECTION_MODE env var selects preset:
  fast    → yolov8n  416px  conf=0.30  10 fps  cpu/gpu  fp32
  precise → yolov8m  640px  conf=0.40   2 fps  cpu/gpu  fp32
  gpu     → yolov8l  640px  conf=0.35  15 fps  gpu-only fp16
"""

import os
import torch
import numpy as np
from ultralytics import YOLO

PRESETS = {
    "fast": {
        "default_model": "/models/yolov8n.pt",
        "imgsz": 416,
        "conf": 0.30,
        "required_fps": 10.0,
        "half": False,
    },
    "precise": {
        "default_model": "/models/yolov8m.pt",
        "imgsz": 640,
        "conf": 0.40,
        "required_fps": 2.0,
        "half": False,
    },
    "gpu": {
        "default_model": "/models/yolov8l.pt",
        "imgsz": 640,
        "conf": 0.32,          # balanced: fewer false-pos than 0.25, still detects on noisy streams
        "required_fps": 15.0,
        "half": False,
    },
}

_DETECTION_MODE = os.getenv("DETECTION_MODE", "fast")
PRESET = PRESETS.get(_DETECTION_MODE, PRESETS["fast"])

_model = None


def get_model():
    global _model

    if _model is None:
        model_path = os.getenv("MODEL_PATH", PRESET["default_model"])
        cuda_ok = torch.cuda.is_available()
        device = "cuda:0" if cuda_ok else "cpu"

        print(f"[YOLO] mode={_DETECTION_MODE}  model={model_path}  device={device}  "
              f"imgsz={PRESET['imgsz']}  conf={PRESET['conf']}  "
              f"fps={PRESET['required_fps']}  fp16={PRESET['half'] and cuda_ok}")

        _model = YOLO(model_path)
        _model.to(device)
        # FP16 applied per-call via half=True in track() — not here

    return _model


def warmup():
    print(f"[YOLO] Warmup (mode={_DETECTION_MODE}, imgsz={PRESET['imgsz']})...")
    model = get_model()
    cuda_ok = torch.cuda.is_available()
    use_half = PRESET["half"] and cuda_ok
    dummy = np.zeros((PRESET["imgsz"], PRESET["imgsz"], 3), dtype=np.uint8)
    model.predict(source=dummy, verbose=False, half=use_half)
    print("[YOLO] Warmup complete")
