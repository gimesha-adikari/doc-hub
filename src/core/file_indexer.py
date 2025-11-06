from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from sqlalchemy.orm import Session
from whoosh.writing import AsyncWriter

from src.core.database import get_session, WatchedFolder, IndexedFile

from tika import parser as tika_parser

from src.core.search_index_service import SearchIndexService

code = {
    '.py', '.java', '.js', '.css', '.html', '.md', '.qss', '.xml',
    '.cpp', '.h', '.hpp', '.c', '.cs', '.php', '.rb', '.go', '.rs',
    '.swift', '.kt', '.scala', '.r', '.sql', '.sh', '.bat', '.ps1',
    '.yaml', '.yml', '.json', '.ts', '.jsx', '.tsx'
}


def extract_content_from_file(file_path: Path) -> (str, str):
    try:
        parsed_data = tika_parser.from_file(str(file_path))

        content = parsed_data.get("content") or ""
        metadata = parsed_data.get("metadata") or {}

        mime_type = metadata.get('Content-Type', 'application/octet-stream')

        display_type = "unsupported"

        if mime_type.startswith("image/"):
            display_type = "image"
        elif mime_type == "application/pdf":
            display_type = ".pdf"
        elif mime_type.startswith('text/'):
            display_type = ".txt"
        elif 'application/vnd.openxmlformats-officedocument' in mime_type:
            display_type = ".docx"
        elif 'application/msword' in mime_type:
            display_type = ".doc"
        elif 'application/json' in mime_type:
            display_type = ".json"
        elif 'application/xml' in mime_type:
            display_type = ".xml"

        suffix = file_path.suffix.lower()
        if suffix in code:
            display_type = suffix

        if not content and display_type.startswith('.'):
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        return display_type, (content or "").strip()

    except Exception as e:
        print(f"Error reading {file_path} with Tika: {e}")

        try:
            suffix = file_path.suffix.lower()
            if suffix in code:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                return suffix, content
        except Exception:
            pass

        return "unsupported", ""


class FileIndexWorker(QObject):
    finished = Signal()
    progress_updated = Signal(str)

    def __init__(self):
        super().__init__()
        self.index_service= SearchIndexService()

    def run_scan(self):
        self.progress_updated.emit("Starting scan...")
        session = get_session()

        writer = self.index_service.get_writer()

        try:
            folders = session.query(WatchedFolder).all()
            if not folders:
                self.progress_updated.emit("No folders to watch. Add folders in Settings.")
                self.finished.emit()
                session.close()
                return

            for folder in folders:
                self.progress_updated.emit(f"Scanning {folder.file_path}...")
                folder_path = Path(folder.file_path)

                for file_path in folder_path.rglob("*"):
                    if not file_path.is_file():
                        continue

                    self._process_file(session, writer, file_path)

            self.progress_updated.emit("Scan completed.")
        except Exception as e:
            print(f"Error during scan: {e}")
            self.progress_updated.emit(f"Error during scan: {e}")
        finally:
            writer.commit()
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

            self.progress_updated.emit(f"Processing {file_path.name}...")

            display_type, content = extract_content_from_file(file_path)

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

            whoosh_record = IndexedFile(
                file_path=str_path,
                file_name=file_path.name,
                extracted_content=content
            )

            self.index_service.add_or_update_document(writer,whoosh_record)
            session.commit()

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            session.rollback()
