from PySide6.QtCore import QObject, QThread, QTimer, QFileSystemWatcher, Signal, Slot
from PySide6.QtWidgets import QStatusBar
from src.doc_hub.core.file_indexer import FileIndexWorker
from src.doc_hub.core.database import get_session, WatchedFolder


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

        self.scan_timer.timeout.connect(self.run_full_scan)
        self.watcher.directoryChanged.connect(self.request_scan)
        self.watcher.fileChanged.connect(self.request_scan)

    @Slot()
    def request_scan(self):
        try:
            self.status_bar.showMessage("Change detected, scan pending...")
        except RuntimeError:
            pass
        self.scan_timer.start()

    def update_watcher_paths(self):
        session = get_session()
        try:
            old_paths = self.watcher.directories()
            if old_paths:
                self.watcher.removePaths(old_paths)

            folders = session.query(WatchedFolder).all()
            new_paths = [f.file_path for f in folders if f.file_path]

            if new_paths:
                self.watcher.addPaths(new_paths)
                print(f"[Watcher] Now watching: {new_paths}")
            else:
                print("[Watcher] No folders to watch.")
        except Exception as e:
            print(f"Error updating watcher paths: {e}")
        finally:
            session.close()

    @Slot()
    def run_full_scan(self):
        if self.indexer_thread and self.indexer_thread.isRunning():
            try:
                self.status_bar.showMessage("Scan already in progress...")
            except RuntimeError:
                pass
            return

        if self.indexer_thread:
            try:
                self.indexer_thread.quit()
                self.indexer_thread.wait(2000)
            except Exception:
                pass
            self.indexer_thread = None
            self.indexer_worker = None

        self.indexer_thread = QThread(parent=self)
        self.indexer_worker = FileIndexWorker()
        self.indexer_worker.moveToThread(self.indexer_thread)

        self.indexer_worker.progress_updated.connect(self.update_status_bar)
        self.indexer_worker.finished.connect(self.on_scan_finished)

        self.indexer_worker.finished.connect(self.indexer_thread.quit)
        self.indexer_thread.finished.connect(self.indexer_thread.deleteLater)

        self.indexer_thread.started.connect(self.indexer_worker.run_scan)
        self.indexer_thread.start()

        try:
            self.status_bar.showMessage("Starting scan...")
        except RuntimeError:
            pass

    @Slot(str)
    def update_status_bar(self, message: str):
        try:
            self.status_bar.showMessage(message)
        except RuntimeError:
            pass

    @Slot()
    def on_scan_finished(self):
        try:
            self.status_bar.showMessage("Scanning completed.", 5000)
        except RuntimeError:
            pass

        if self.indexer_thread:
            if self.indexer_thread.isRunning():
                self.indexer_thread.quit()
                self.indexer_thread.wait(2000)

            self.indexer_thread = None
            self.indexer_worker = None

        try:
            self.update_watcher_paths()
        except Exception as e:
            print(f"Watcher update failed after scan: {e}")

        self.scan_finished.emit()
