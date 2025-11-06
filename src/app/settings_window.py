import fileinput

from PySide6.QtWidgets import QDialog, QFileDialog

from src.core.database import get_session, WatchedFolder, IndexedFile
from src.core.search_index_service import SearchIndexService
from src.ui.settings_window_ui import Ui_SettingsWindow


class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = Ui_SettingsWindow()
        self.ui.setupUi(self)

        self.ui.add_folder_button.clicked.connect(self.add_folder)
        self.ui.remove_folder_button.clicked.connect(self.remove_folder)
        self.ui.close_button.clicked.connect(self.close)

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

        index_service = SearchIndexService()
        writer = index_service.get_writer()
        session = get_session()

        try:
            search_pattern = f"{folder_path}%"
            files_to_delete_query = session.query(IndexedFile).filter(IndexedFile.file_path.like(search_pattern))
            file_paths_to_delete = [f.file_path for f in files_to_delete_query.all()]

            for path in file_paths_to_delete:
                index_service.delete_document_by_path(writer,path)

            files_to_delete_query.delete(synchronize_session=False)

            folder_to_delete = session.query(WatchedFolder).filter_by(file_path=folder_path).first()
            if folder_to_delete:
                session.delete(folder_to_delete)

            session.commit()
            writer.commit()

            self.load_watched_folders()

        except Exception as e:
            print(f"Error removing folder and its files: {e}")
            session.rollback()
            writer.cancel()

        finally:
            session.close()