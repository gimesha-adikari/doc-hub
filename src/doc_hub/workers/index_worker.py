from PySide6.QtCore import QThread, Signal
from src.doc_hub.core.incremental_indexer import IncrementalIndexer
import traceback

class IndexWorker(QThread):
    progress = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, paths, drop_removed=False):
        super().__init__()
        self.paths = paths
        self.drop_removed = drop_removed

    def run(self):
        try:
            indexer = IncrementalIndexer(self.paths)
            self.progress.emit("Reindexing started...")
            indexer.reindex()
            if self.drop_removed:
                self.progress.emit("Removing deleted files...")
                indexer.drop_removed()
            self.finished.emit(True, "Reindexing completed successfully.")
        except Exception as e:
            traceback.print_exc()
            self.finished.emit(False, str(e))
