import os
import fnmatch
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from sqlalchemy.orm import Session
from whoosh.writing import AsyncWriter

from src.core.database import get_session, WatchedFolder, IndexedFile

from tika import parser as tika_parser

from src.core.search_index_service import SearchIndexService

IGNORED_DIRS = {
    '.git', '.hg', '.svn',
    '.idea', '.vs', '.vscode',
    'node_modules', '.next', '.nuxt', '.cache', '.parcel-cache', '.vite',
    '.svelte-kit', '.angular', '.yarn', '.pnp', '.pnpm-store', '.vercel',
    '.netlify', '.docusaurus',
    '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.tox',
    '.ipynb_checkpoints', '.venv', 'venv', 'env', '.eggs',
    '.gradle', '.build', 'build', 'out', 'libs',
    'Pods', 'DerivedData',
    'bin', 'obj',
    'target',
    '.terraform', '.serverless', '.firebase', '.expo', '.dart_tool',
    'temp', 'tmp', 'logs'
}

IGNORED_DIR_GLOBS = [
    '*.egg-info'
]

IGNORED_FILES = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'bun.lockb',
    'Pipfile.lock', 'poetry.lock', 'composer.lock', 'Gemfile.lock', 'Cargo.lock',
    '.DS_Store', 'Thumbs.db', 'desktop.ini',
    'gradle-wrapper.jar', '.coverage'
}

IGNORED_FILE_GLOBS = [
    '.coverage.*',
    '*.pyc', '*.pyo', '*.pyd',
    '*.class',
    '*.o', '*.obj', '*.a', '*.so', '*.dll', '*.dylib',
    '*.min.*.map',
    '.env.*.local', '*.local.env', '.env',
    '*.log', '*.tmp', '*.temp',
    'stats.*.json', 'stats.json',
]

CODE_EXTENSIONS = {
    '.py', '.java', '.js', '.css', '.html', '.md', '.qss', '.xml',
    '.cpp', '.h', '.hpp', '.c', '.cs', '.php', '.rb', '.go', '.rs',
    '.swift', '.kt', '.scala', '.r', '.sql', '.sh', '.bat', '.ps1',
    '.yaml', '.yml', '.json', '.ts', '.jsx', '.tsx'
}

TEXT_EXTENSIONS = {
    '.txt', '.ini', '.cfg', '.conf', '.properties', '.toml'
}

COMPLEX_MIME_PREFIXES = (
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
)


def extract_content_from_file(file_path: Path) -> (str, str):
    suffix = file_path.suffix.lower()

    if suffix in CODE_EXTENSIONS or suffix in TEXT_EXTENSIONS:
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            display_type = suffix if suffix else ".txt"
            return display_type, content.strip()
        except Exception as e:
            print(f"Error reading plain text file {file_path}: {e}")
            return "unsupported", ""

    try:
        parsed_data = tika_parser.from_file(str(file_path))
        content = parsed_data.get("content") or ""
        metadata = parsed_data.get("metadata") or {}
        mime_type = metadata.get('Content-Type', 'application/octet-stream')

        if mime_type.startswith("image/"):
            return "image", ""

        if mime_type.startswith(COMPLEX_MIME_PREFIXES):
            if suffix and suffix in CODE_EXTENSIONS:
                display_type = suffix
            elif mime_type == "application/pdf":
                display_type = ".pdf"
            elif 'application/vnd.openxmlformats-officedocument' in mime_type:
                display_type = ".docx"
            elif 'application/msword' in mime_type:
                display_type = ".doc"
            else:
                display_type = suffix if suffix else "unsupported"

            return display_type, content.strip()

        if content:
            return ".txt", content.strip()

        return f"unsupported ({suffix})", ""

    except Exception as e:
        print(f"Error reading {file_path} with Tika: {e}")
        return f"unsupported ({suffix})", ""


class FileIndexWorker(QObject):
    finished = Signal()
    progress_updated = Signal(str)

    def __init__(self):
        super().__init__()
        self.index_service = SearchIndexService()

    def _is_dir_ignored(self, dir_name: str) -> bool:
        if dir_name in IGNORED_DIRS:
            return True
        for pattern in IGNORED_DIR_GLOBS:
            if fnmatch.fnmatch(dir_name, pattern):
                return True
        return False

    def _is_file_ignored(self, file_name: str) -> bool:
        if file_name in IGNORED_FILES:
            return True
        for pattern in IGNORED_FILE_GLOBS:
            if fnmatch.fnmatch(file_name, pattern):
                return True
        return False

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

                for root, dirs, files in os.walk(folder.file_path, topdown=True):
                    dirs[:] = [d for d in dirs if not self._is_dir_ignored(d)]

                    for filename in files:
                        if self._is_file_ignored(filename):
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

            if display_type.startswith("unsupported"):
                return

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

            if content:
                whoosh_record = IndexedFile(
                    file_path=str_path,
                    file_name=file_path.name,
                    extracted_content=content
                )
                self.index_service.add_or_update_document(writer, whoosh_record)

            session.commit()

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            session.rollback()