from PySide6.QtCore import QThread, Signal
import requests, traceback

class ModelWorker(QThread):
    result = Signal(str)
    error = Signal(str)

    def __init__(self, prompt, parent=None):
        super().__init__(parent)
        self.prompt = prompt

    def run(self):
        try:
            r = requests.post(
                "http://127.0.0.1:7860/generate",
                json={"prompt": self.prompt, "max_tokens": 200},
                timeout=120
            )
            if r.status_code == 200:
                self.result.emit(r.json().get("text", ""))
            else:
                self.error.emit(f"HTTP {r.status_code}: {r.text}")
        except Exception:
            self.error.emit(traceback.format_exc())
