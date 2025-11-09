import os
from datetime import datetime, UTC
from pathlib import Path
from PySide6.QtCore import QObject, Signal
from sqlalchemy.orm import Session
from whoosh.writing import AsyncWriter
from src.doc_hub.core.database import get_session, WatchedFolder, IndexedFile, DATABASE_DIR
from src.doc_hub.core.search_index_service import SearchIndexService
from src.doc_hub.core.ai_service import AIService
from src.doc_hub.core.file_processing import extract_content_from_file, is_dir_ignored, is_file_ignored

INDEX_LOG_FILE = os.path.join(DATABASE_DIR, "indexed_files.log")

class FileIndexWorker(QObject):
    finished = Signal()
    progress_updated = Signal(str)

    def __init__(self):
        super().__init__()
        self.index_service = SearchIndexService()
        self.ai_service = AIService()

    def run_scan(self):
        self.progress_updated.emit("Starting full scan...")
        session = get_session()
        writer = self.index_service.get_writer()
        if writer is None:
            self.progress_updated.emit("Could not acquire Whoosh writer. Skipping scan.")
            self.finished.emit()
            session.close()
            return
        try:
            with open(INDEX_LOG_FILE, "w", encoding="utf-8") as f:
                f.write(f"--- Scan started at {datetime.now(UTC)} ---\n")

            folders = session.query(WatchedFolder).all()
            if not folders:
                self.progress_updated.emit("No watched folders found. Add one in Settings.")
                self.finished.emit()
                session.close()
                return

            for folder in folders:
                folder_path = folder.file_path
                if not os.path.exists(folder_path):
                    self.progress_updated.emit(f"Skipping missing folder: {folder_path}")
                    continue

                self.progress_updated.emit(f"Scanning {folder_path}...")
                for root, dirs, files in os.walk(folder_path, topdown=True):
                    dirs[:] = [d for d in dirs if not is_dir_ignored(d)]
                    for filename in files:
                        if is_file_ignored(filename):
                            continue
                        try:
                            file_path = Path(os.path.join(root, filename))
                            if file_path.is_file():
                                self._process_file(session, writer, file_path)
                        except (OSError, FileNotFoundError) as e:
                            print(f"Skipping file {filename}: {e}")

            self.progress_updated.emit("Scan completed successfully.")
        except Exception as e:
            print(f"Error during scan: {e}")
            self.progress_updated.emit(f"Error during scan: {e}")
        finally:
            try:
                self.index_service.commit_writer(writer)
            except Exception as e:
                print(f"Error committing writer: {e}")
            if session.is_active:
                session.close()
            self.finished.emit()

    def _process_file(self, session: Session, writer: AsyncWriter, file_path: Path):
        try:
            str_path = str(file_path)
            stats = file_path.stat()
            file_mod_time = datetime.fromtimestamp(stats.st_mtime, UTC)
            file_size = stats.st_size

            existing_file = session.query(IndexedFile).filter_by(file_path=str_path).first()
            if existing_file and existing_file.date_modified >= file_mod_time:
                return

            display_type, content, ai_eligible = extract_content_from_file(file_path)
            if not content or display_type.startswith("unsupported"):
                return

            ai_tags = ""
            ai_summary = ""
            if ai_eligible:
                try:
                    self.progress_updated.emit(f"Generating AI tags for {file_path.name}...")
                    ai_tags, ai_summary = self.ai_service.get_tags_and_summary(content)
                except Exception as e:
                    print(f"AI tagging skipped/failed for {file_path}: {e}")

            self.progress_updated.emit(f"Processing {file_path.name}...")

            if not existing_file:
                new_file = IndexedFile(
                    file_name=file_path.name,
                    file_path=str_path,
                    file_type=display_type,
                    file_size=file_size,
                    date_modified=file_mod_time,
                    extracted_content="",
                    ai_tags="",
                    ai_summary=""
                )
                session.add(new_file)
                session.flush()
            else:
                existing_file.file_name = file_path.name
                existing_file.file_type = display_type
                existing_file.file_size = file_size
                existing_file.date_modified = file_mod_time
                existing_file.extracted_content = ""
                existing_file.ai_tags = ""
                existing_file.ai_summary = ""
                existing_file.date_indexed = datetime.now(UTC)
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
                new_file.date_indexed = datetime.now(UTC)
                session.commit()

                self.index_service.add_or_update_document(writer, new_file, ai_tags, ai_summary)

                try:
                    with open(INDEX_LOG_FILE, "a", encoding="utf-8") as f:
                        f.write(f"{str_path}\n")
                except Exception as log_e:
                    print(f"Failed to write to index log file: {log_e}")

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            session.rollback()
