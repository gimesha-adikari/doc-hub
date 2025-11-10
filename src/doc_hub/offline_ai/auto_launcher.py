import subprocess
import time
import requests
import os
from pathlib import Path


def is_server_alive() -> bool:
    try:
        r = requests.get("http://127.0.0.1:7860/docs", timeout=1)
        return r.ok
    except Exception:
        return False


def launch_local_model(model_name: str = "phi-2"):
    if is_server_alive():
        print("✅ Local AI server already running.")
        return True

    script_path = Path(__file__).parent / "launch_model.sh"
    if not script_path.exists():
        print("❌ launch_model.sh not found.")
        return False

    try:
        env = os.environ.copy()
        cmd = ["bash", str(script_path), model_name]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"🚀 Starting local AI model: {model_name} ...")

        for _ in range(180):
            print(f"⏳ Waiting for local model ({model_name}) to start... ({_ + 1}/180)")
            if is_server_alive():
                print("✅ Local AI model ready!")
                return True
            time.sleep(1)

        print("⚠️ Local AI model did not start in time.")
        return False
    except Exception as e:
        print(f"❌ Failed to launch local model: {e}")
        return False
