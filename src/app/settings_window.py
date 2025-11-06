import fileinput

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QDialog, QFileDialog, QLabel

from src.core.database import get_session, WatchedFolder, IndexedFile
from src.ui.settings_window_ui import Ui_SettingsWindow
from src.core.delete_worker import DeleteFolderWorker


class SettingsWindow(QDialog):
    deletion_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_SettingsWindow()
        self.ui.setupUi(self)

        self.ui.status_label = QLabel("")
        self.ui.status_label.setStyleSheet("color: #8a8a8a;")
        self.ui.verticalLayout.insertWidget(2, self.ui.status_label)

        self.ui.add_folder_button.clicked.connect(self.add_folder)
        self.ui.remove_folder_button.clicked.connect(self.remove_folder)
        self.ui.close_button.clicked.connect(self.close)

        self.delete_thread = QThread()
        self.delete_worker = DeleteFolderWorker()
        self.delete_worker.moveToThread(self.delete_thread)

        self.deletion_requested.connect(self.delete_worker.run_delete)
        self.delete_worker.progress.connect(self.update_status)
        self.delete_worker.finished.connect(self.on_delete_finished)

        self.delete_thread.start()

        self.load_watched_folders()

    def load_watched_folders(self):
        self.ui.folders_list_widget.clear()

        session = get_session()
        try:
            folders = session.query(WatchedFolder).all()
            for folder in folders:
                self.ui.folders_list_widget.addItem(folder.file_path)
        finally:
            session.close()

    def add_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to watch")
        if folder_path:
            session = get_session()
            try:
                exists = session.query(WatchedFolder).filter_by(file_path=folder_path).first()
                if not exists:
                    new_folder = WatchedFolder(file_path=folder_path)
                    session.add(new_folder)
                    session.commit()

                    self.load_watched_folders()
            except Exception as e:
                print(f"Error adding folder: {e}")
                session.rollback()
            finally:
                session.close()

    def remove_folder(self):
        current_item = self.ui.folders_list_widget.currentItem()
        if not current_item:
            return
        folder_path = current_item.text()

        self.set_ui_enabled(False)
        self.update_status(f"Requesting deletion of {folder_path}...")
        self.deletion_requested.emit(folder_path)

    def update_status(self, message: str):
        self.ui.status_label.setText(message)

    def on_delete_finished(self):
        self.set_ui_enabled(True)
        self.load_watched_folders()
        self.update_status("Task finished.")

    def set_ui_enabled(self, enabled: bool):
        self.ui.add_folder_button.setEnabled(enabled)
        self.ui.remove_folder_button.setEnabled(enabled)
        self.ui.close_button.setEnabled(enabled)

    def close(self):
        self.delete_thread.quit()
        self.delete_thread.wait()
        super().close()