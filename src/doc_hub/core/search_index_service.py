import os
from whoosh.fields import Schema, ID, TEXT, DATETIME
from whoosh.index import create_in, open_dir, exists_in
from whoosh.writing import AsyncWriter

from doc_hub.core.database import DATABASE_DIR

INDEX_DIR = os.path.join(DATABASE_DIR, "whoosh_index")


def get_index_schema():
    """
    Defines the Whoosh index schema.
    """
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
            return create_in(self.index_dir, self.schema)

        if exists_in(self.index_dir):
            return open_dir(self.index_dir)
        else:
            return create_in(self.index_dir, self.schema)

    def get_writer(self) -> AsyncWriter:
        return self.ix.writer()

    def add_or_update_document(self, writer: AsyncWriter, file_record, ai_tags: str, ai_summary: str):
        writer.update_document(
            file_path=file_record.file_path,
            file_name=file_record.file_name,
            content=file_record.extracted_content,
            date_indexed=file_record.date_indexed,

            ai_tags=ai_tags,
            ai_summary=ai_summary
        )

    def delete_document_by_path(self, writer: AsyncWriter, file_path: str):
        writer.delete_by_term('file_path', file_path)