import os

from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import Schema, ID, TEXT, STORED
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.writing import AsyncWriter

from src.core.database import IndexedFile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDEX_DIR = os.path.join(BASE_DIR, "database", "whoosh_index")

class SearchIndexService:
    def __init__(self):
        self.schema = Schema(
            file_path = ID(stored=True, unique=True),
            file_name=TEXT(stored=True),
            content = TEXT(stored=True)
        )

        if not os.path.exists(INDEX_DIR):
            os.makedirs(INDEX_DIR)
            self.ix = create_in(INDEX_DIR, self.schema)
        else:
            self.ix = open_dir(INDEX_DIR)

    def get_writer(self) -> AsyncWriter:
        return AsyncWriter(self.ix)

    def add_or_update_document(self, writer: AsyncWriter, file_record: IndexedFile):
        writer.update_document(
            file_path=file_record.file_path,
            file_name = file_record.file_name,
            content=file_record.extracted_content
        )

    def delete_document_by_path(self, writer: AsyncWriter, file_path:str):
        writer.delete_by_term("file_path",file_path)

    def search(self, fts_query: str, keywords: list[str])->list[str]:
        if not fts_query:
            return []

        try:
            with self.ix.searcher() as searcher:
                parser = MultifieldParser(["file_name","content"], self.ix.schema)

                query_string = " AND ".join(keywords)

                query = parser.parse(query_string)

                results = searcher.search(query,limit=100)

                return [hit['file_path'] for hit in results]

        except Exception as e:
            print(f"Error during Whoosh search: {e}")
            return []

