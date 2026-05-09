#!/usr/bin/env python3
"""Pre-download all Ultralytics model weights to local cache.
Run this before starting the pipeline to avoid runtime download delays.
"""
import os
import sys
from pathlib import Path

def download_models(output_dir: str = "./cv-pipeline/models"):
    """Download all required model weights from Ultralytics hub."""
    try:
        from ultralytics import YOLO
    except ImportError:
        print("❌ ultralytics not installed. Run: pip install ultralytics")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    models = {
        "yolov8n.pt": "detection",
        "yolov8n-pose.pt": "pose estimation",
        "yolov8n-seg.pt": "segmentation",
        "yolov8n-cls.pt": "classification",
    }

    print("📦 Downloading Ultralytics model weights...")
    print(f"   Target directory: {os.path.abspath(output_dir)}\n")

    for model_name, purpose in models.items():
        model_path = os.path.join(output_dir, model_name)
        if os.path.exists(model_path):
            size_mb = os.path.getsize(model_path) / (1024 * 1024)
            print(f"   ✅ {model_name} already exists ({size_mb:.1f} MB) — {purpose}")
            continue

        print(f"   ⬇️  Downloading {model_name} ({purpose})...")
        try:
            model = YOLO(model_name)
            # Force download by running a dummy predict
            dummy = model.predict("https://ultralytics.com/images/bus.jpg", verbose=False)
            # The model file is now cached in output_dir or ~/.ultralytics/
            # Copy to our local dir if it ended up elsewhere
            ultralytics_cache = Path.home() / ".ultralytics" / "models" / model_name
            if ultralytics_cache.exists() and not os.path.exists(model_path):
                import shutil
                shutil.copy(str(ultralytics_cache), model_path)
                print(f"   ✅ {model_name} downloaded and cached")
            elif os.path.exists(model_path):
                print(f"   ✅ {model_name} downloaded")
            else:
                print(f"   ⚠️  {model_name} may be in ~/.ultralytics/models/")
        except Exception as e:
            print(f"   ❌ Failed to download {model_name}: {e}")

    print("\n🎉 Model download complete!")
    print(f"   Models directory: {os.path.abspath(output_dir)}")
    print("   You can now start the pipeline with: ./start-demo.sh")


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "./cv-pipeline/models"
    download_models(output)
