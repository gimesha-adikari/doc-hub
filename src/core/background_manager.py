from PySide6.QtCore import QObject, QThread, QTimer, QFileSystemWatcher, Signal
from PySide6.QtWidgets import QStatusBar
from src.core.file_indexer import FileIndexWorker
from src.core.database import get_session, WatchedFolder


class BackgroundManager(QObject):
    scan_finished = Signal()

    def __init__(self, status_bar: QStatusBar, parent=None):
        super().__init__(parent)

        self.status_bar = status_bar
        self.indexer_thread = None
        self.indexer_worker = None

        self.watcher = QFileSystemWatcher(self)
        self.scan_timer = QTimer(self)

        self.scan_timer.setSingleShot(True)
        self.scan_timer.setInterval(5000)

        # Connect signals
        self.scan_timer.timeout.connect(self.run_full_scan)
        self.watcher.directoryChanged.connect(self.request_scan)
        self.watcher.fileChanged.connect(self.request_scan)

    def request_scan(self):
        self.status_bar.showMessage("Change detected, scan pending...")
        self.scan_timer.start()

    def update_watcher_paths(self):
        session = get_session()
        try:
            old_paths = self.watcher.directories()
            if old_paths:
                self.watcher.removePaths(old_paths)

            folders = session.query(WatchedFolder).all()
            new_paths = [folder.file_path for folder in folders]
            if new_paths:
                self.watcher.addPaths(new_paths)
                print(f"Now watching: {new_paths}")

        except Exception as e:
            print(f"Error updating watcher paths: {e}")
        finally:
            session.close()

    def run_full_scan(self):
        if self.indexer_thread and self.indexer_thread.isRunning():
            self.status_bar.showMessage("Scan already in progress...")
            return

        self.indexer_thread = QThread()
        self.indexer_worker = FileIndexWorker()
        self.indexer_worker.moveToThread(self.indexer_thread)

        self.indexer_worker.progress_updated.connect(self.update_status_bar)
        self.indexer_worker.finished.connect(self.on_scan_finished)

        self.indexer_thread.started.connect(self.indexer_worker.run_scan)

        self.indexer_thread.start()

        self.status_bar.showMessage("Starting scan...")

    def update_status_bar(self, message: str):
        self.status_bar.showMessage(message)

    def on_scan_finished(self):
        self.status_bar.showMessage("Scanning completed.", 5000)

        if self.indexer_thread:
            self.indexer_thread.quit()
            self.indexer_thread.wait()
            self.indexer_thread = None
            self.indexer_worker = None

        self.update_watcher_paths()
        self.scan_finished.emit()