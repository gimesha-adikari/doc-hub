import os
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QObject, Signal
from sqlalchemy.orm import Session
from whoosh.writing import AsyncWriter
from doc_hub.core.database import get_session, WatchedFolder, IndexedFile, DATABASE_DIR
from doc_hub.core.search_index_service import SearchIndexService
from doc_hub.core.ai_service import AIService
from doc_hub.core.file_processing import extract_content_from_file, is_dir_ignored, is_file_ignored

INDEX_LOG_FILE = os.path.join(DATABASE_DIR, "indexed_files.log")

class FileIndexWorker(QObject):
    finished = Signal()
    progress_updated = Signal(str)

    def __init__(self):
        super().__init__()
        self.index_service = SearchIndexService()
        self.ai_service = AIService()

    def run_scan(self):
        self.progress_updated.emit("Starting scan...")
        session = get_session()
        writer = self.index_service.get_writer()
        try:
            try:
                with open(INDEX_LOG_FILE, "w", encoding="utf-8") as f:
                    f.write(f"--- Scan started at {datetime.now()} ---\n")
            except Exception as log_e:
                print(f"Failed to clear log file: {log_e}")

            folders = session.query(WatchedFolder).all()
            if not folders:
                self.progress_updated.emit("No folders to watch. Add folders in Settings.")
                self.finished.emit()
                session.close()
                return

            for folder in folders:
                self.progress_updated.emit(f"Scanning {folder.file_path}...")
                for root, dirs, files in os.walk(folder.file_path, topdown=True):
                    dirs[:] = [d for d in dirs if not is_dir_ignored(d)]
                    for filename in files:
                        if is_file_ignored(filename):
                            continue
                        try:
                            file_path = Path(os.path.join(root, filename))
                            if not file_path.is_file():
                                continue
                            self._process_file(session, writer, file_path)
                        except (OSError, FileNotFoundError) as e:
                            print(f"Skipping file {filename}: {e}")

            self.progress_updated.emit("Scan completed.")
        except Exception as e:
            print(f"Error during scan: {e}")
            self.progress_updated.emit(f"Error during scan: {e}")
        finally:
            try:
                if writer is not None:
                    writer.commit()
            except Exception as e:
                print(f"Error committing writer: {e}")
            if session.is_active:
                session.close()
            self.finished.emit()

    def _process_file(self, session: Session, writer: AsyncWriter, file_path: Path):
        try:
            str_path = str(file_path)
            stats = file_path.stat()
            file_mod_time = datetime.fromtimestamp(stats.st_mtime)
            file_size = stats.st_size

            existing_file = session.query(IndexedFile).filter_by(file_path=str_path).first()
            if existing_file:
                if existing_file.date_modified >= file_mod_time:
                    return

            display_type, content = extract_content_from_file(file_path)
            if display_type.startswith("unsupported") or display_type == "image":
                return

            self.progress_updated.emit(f"Processing {file_path.name}...")

            if not existing_file:
                new_file = IndexedFile(
                    file_name=file_path.name,
                    file_path=str_path,
                    file_type=display_type,
                    file_size=file_size,
                    date_modified=file_mod_time,
                    extracted_content=""
                )
                session.add(new_file)
                session.flush()
            else:
                existing_file.file_name = file_path.name
                existing_file.file_type = display_type
                existing_file.file_size = file_size
                existing_file.date_modified = file_mod_time
                existing_file.extracted_content = ""
                existing_file.date_indexed = datetime.now()
                new_file = existing_file

            session.commit()

            if content:
                ai_tags = ""
                ai_summary = ""
                try:
                    self.progress_updated.emit(f"Generating AI tags for {file_path.name}...")
                    ai_tags, ai_summary = self.ai_service.get_tags_and_summary(content)
                except Exception as e:
                    print(f"AI tagging failed for {file_path}: {e}")

                new_file.extracted_content = content
                new_file.ai_tags = ai_tags
                new_file.ai_summary = ai_summary
                new_file.date_indexed = datetime.now()
                session.commit()

                self.index_service.add_or_update_document(
                    writer,
                    new_file,
                    ai_tags,
                    ai_summary
                )

                try:
                    with open(INDEX_LOG_FILE, "a", encoding="utf-8") as f:
                        f.write(f"{str_path}\n")
                except Exception as log_e:
                    print(f"Failed to write to log file: {log_e}")

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            session.rollback()
