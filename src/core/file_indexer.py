import os
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from pypdf import PdfReader
from sqlalchemy.orm import Session

from src.core.database import get_session, WatchedFolder, IndexedFile


def extract_pdf_text(file_path: Path) -> str:
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or "" + " "
        return text
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return ""


IMAGE_TYPES = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg'
}

TEXT_TYPES = {
    '.txt', '.md', '.py', '.java', '.qss', '.xml', '.html', '.css', '.js'
}


class FileIndexWorker(QObject):
    finished = Signal()
    progress_updated = Signal(str)

    def __init__(self):
        super().__init__()

    def run_scan(self):
        self.progress_updated.emit("Starting scan...")
        session = get_session()

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

                    self._process_file(session, file_path)

            self.progress_updated.emit("Scan completed.")
        except Exception as e:
            print(f"Error during scan: {e}")
            self.progress_updated.emit(f"Error during scan: {e}")
        finally:
            if session.is_active:
                session.close()
            self.finished.emit()

    def _process_file(self, session: Session, file_path: Path):

        try:
            str_path = str(file_path)

            stats = file_path.stat()
            file_mod_time = datetime.fromtimestamp(stats.st_mtime)
            file_size = stats.st_size

            existing_file = session.query(IndexedFile).filter_by(file_path=str_path).first()
            if existing_file:
                if existing_file.date_modified >= file_mod_time:
                    return

            self.progress_updated.emit(f"Processing {file_path}...")
            file_type = file_path.suffix.lower()
            content = ""
            if file_type == ".pdf":
                content = extract_pdf_text(file_path)
                display_type = ".pdf"
            elif file_type in TEXT_TYPES:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                display_type = file_type
            elif file_type in IMAGE_TYPES:
                display_type = "image"
            else:
                display_type = f"unsupported ({file_type})"

            if not existing_file:
                new_file = IndexedFile(
                    file_name=file_path.name,
                    file_path=str_path,
                    file_type=display_type,
                    file_size=file_size,
                    date_modified=file_mod_time,
                    extracted_content=content
                )
                session.add(new_file)
            else:
                existing_file.file_name = file_path.name
                existing_file.file_type = display_type
                existing_file.file_size = file_size
                existing_file.date_modified = file_mod_time
                existing_file.extracted_content = content
                existing_file.date_indexed = datetime.now()

            session.commit()

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            session.rollback()
