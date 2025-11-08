from PySide6.QtCore import QObject, Signal, Slot
from doc_hub.core.database import get_session, WatchedFolder, IndexedFile
from doc_hub.core.search_index_service import SearchIndexService


class DeleteFolderWorker(QObject):
    progress = Signal(str)
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.index_service = SearchIndexService()

    @Slot(str)
    def run_delete(self, folder_path: str):
        self.progress.emit("Starting deletion...")
        writer = self.index_service.get_writer()
        session = get_session()

        try:
            search_pattern = f"{folder_path}%"
            self.progress.emit(f"Querying files in {folder_path}...")

            files_to_delete_query = session.query(IndexedFile).filter(
                IndexedFile.file_path.like(search_pattern)
            )
            file_paths_to_delete = [f.file_path for f in files_to_delete_query.all()]

            if not file_paths_to_delete:
                self.progress.emit("No files found to delete.")
            else:
                self.progress.emit(f"Deleting {len(file_paths_to_delete)} files from search index...")

                for i, path in enumerate(file_paths_to_delete):
                    self.index_service.delete_document_by_path(writer, path)
                    if i % 100 == 0:
                        self.progress.emit(f"Deleted {i}/{len(file_paths_to_delete)} from index...")

            self.progress.emit("Deleting files from database...")
            files_to_delete_query.delete(synchronize_session=False)

            folder_to_delete = session.query(WatchedFolder).filter_by(file_path=folder_path).first()
            if folder_to_delete:
                session.delete(folder_to_delete)

            self.progress.emit("Committing changes...")
            session.commit()
            writer.commit()
            self.progress.emit("Deletion complete.")

        except Exception as e:
            print(f"Error removing folder and its files: {e}")
            self.progress.emit(f"Error: {e}")
            session.rollback()
            writer.cancel()
        finally:
            session.close()
            self.finished.emit()