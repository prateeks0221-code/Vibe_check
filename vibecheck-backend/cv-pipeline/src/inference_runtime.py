"""YOLO model lifecycle manager. Loads once, shared across processors."""
import os
import logging

logger = logging.getLogger(__name__)

_models = {}

DUMMY_MODE = os.getenv("DUMMY_MODE", "true").lower() == "true"
MODEL_DIR = os.getenv("MODEL_DIR", "/app/models")


def get_model(model_name: str = "yolov8n"):
    if DUMMY_MODE:
        return None
    if model_name in _models:
        return _models[model_name]
    try:
        from ultralytics import YOLO
        path = os.path.join(MODEL_DIR, f"{model_name}.pt")
        if not os.path.exists(path):
            logger.warning(f"Model file not found: {path}, downloading...")
            model = YOLO(model_name)
        else:
            model = YOLO(path)
        _models[model_name] = model
        logger.info(f"Loaded model: {model_name}")
        return model
    except Exception:
        logger.exception(f"Failed to load model {model_name}")
        return None


def warmup():
    if DUMMY_MODE:
        logger.info("DUMMY_MODE: skipping model warmup")
        return
    get_model("yolov8n")
