from PySide6.QtCore import QThread, Signal
from src.doc_hub.core.duplicate_detector import DuplicateDetector
import traceback

class DuplicateWorker(QThread):
    progress = Signal(str)
    finished = Signal(bool, str, str)

    def __init__(self, paths):
        super().__init__()
        self.paths = paths

    def run(self):
        try:
            self.progress.emit("Scanning for duplicates...")
            detector = DuplicateDetector(self.paths)
            report_path, group_count = detector.find_duplicates()
            msg = f"Found {group_count} duplicate group(s)."
            self.finished.emit(True, msg, str(report_path))
        except Exception as e:
            traceback.print_exc()
            self.finished.emit(False, str(e), "")
