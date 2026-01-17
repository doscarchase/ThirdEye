# doscarchase/thirdeye/setup_sentry.py
import urllib.request
import os

MODEL_URL = "https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_nano.onnx"
DEST_DIR = "assets"
DEST_PATH = os.path.join(DEST_DIR, "sentry_model.onnx")

def download_model():
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)
        
    print(f"Downloading YOLOX-Nano Sentry Core...")
    print(f"Source: {MODEL_URL}")
    
    try:
        urllib.request.urlretrieve(MODEL_URL, DEST_PATH)
        print(f"✅ Success! Model saved to: {DEST_PATH}")
        print("You can now run ThirdEye with the updated Sentry Engine.")
    except Exception as e:
        print(f"❌ Error downloading model: {e}")

if __name__ == "__main__":
    download_model()