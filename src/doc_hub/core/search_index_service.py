import os
import time
import logging
from datetime import datetime, UTC
from whoosh.fields import Schema, ID, TEXT, DATETIME
from whoosh.index import create_in, open_dir, exists_in, LockError
from whoosh.writing import AsyncWriter
from src.doc_hub.core.database import DATABASE_DIR

INDEX_DIR = os.path.join(DATABASE_DIR, "whoosh_index")
LOG_FILE = os.path.join(DATABASE_DIR, "index.log")

os.makedirs(DATABASE_DIR, exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def get_index_schema():
    return Schema(
        file_path=ID(stored=True, unique=True),
        file_name=TEXT(stored=True),
        content=TEXT(stored=True),
        date_indexed=DATETIME(stored=True, sortable=True),
        ai_tags=TEXT(stored=True),
        ai_summary=TEXT(stored=True)
    )

class SearchIndexService:
    def __init__(self):
        self.index_dir = INDEX_DIR
        self.schema = get_index_schema()
        self.ix = self._open_index()

    def _open_index(self):
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)
            logging.info("Created new index directory: %s", self.index_dir)
            return create_in(self.index_dir, self.schema)
        if exists_in(self.index_dir):
            logging.info("Loaded existing Whoosh index.")
            return open_dir(self.index_dir)
        logging.warning("Index not found — creating new index.")
        return create_in(self.index_dir, self.schema)

    def get_writer(self, retries=3, delay=2, use_async=True):
        for attempt in range(retries):
            try:
                writer = AsyncWriter(self.ix) if use_async else self.ix.writer()
                logging.info("Whoosh writer acquired (attempt %d).", attempt + 1)
                return writer
            except LockError:
                logging.warning(
                    "Whoosh index locked (attempt %d/%d), retrying in %ds...",
                    attempt + 1, retries, delay
                )
                time.sleep(delay)
        logging.error("Failed to acquire Whoosh writer after retries.")
        return None

    @staticmethod
    def add_or_update_document(writer, file_record, ai_tags: str = "", ai_summary: str = ""):
        if writer is None:
            logging.warning("Skipped add/update: writer unavailable.")
            return
        try:
            writer.update_document(
                file_path=file_record.file_path,
                file_name=file_record.file_name,
                content=file_record.extracted_content or "",
                date_indexed=file_record.date_indexed or datetime.now(UTC),
                ai_tags=ai_tags or "",
                ai_summary=ai_summary or ""
            )
            logging.info("Indexed or updated file: %s", file_record.file_path)
        except Exception as e:
            logging.error("Failed to index %s: %s", file_record.file_path, e)

    @staticmethod
    def delete_document_by_path(writer, file_path: str):
        if writer is None:
            logging.warning("Skipped delete: writer unavailable.")
            return
        try:
            writer.delete_by_term("file_path", file_path)
            logging.info("Deleted file from index: %s", file_path)
        except Exception as e:
            logging.error("Failed to delete %s: %s", file_path, e)

    @staticmethod
    def commit_writer(writer):
        if writer is None:
            logging.warning("Skipped commit: writer unavailable.")
            return
        try:
            writer.commit()
            logging.info("Whoosh index committed successfully.")
        except Exception as e:
            logging.error("Failed to commit index: %s", e)
