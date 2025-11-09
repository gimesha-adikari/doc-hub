import os
from typing import List, Optional, Set, Tuple, Union
from sqlalchemy import select, desc, not_, or_
from whoosh import index as whoosh_index
from whoosh.fields import Schema, ID, TEXT, DATETIME
from whoosh.qparser import MultifieldParser, WildcardPlugin
from whoosh.query import And, Prefix
from src.doc_hub.core.database import get_session, IndexedFile
from src.doc_hub.core.search_index_service import INDEX_DIR


class SearchService:
    def __init__(self):
        self.index_dir = INDEX_DIR
        self.schema = Schema(
            file_path=ID(stored=True, unique=True),
            file_name=TEXT(stored=True),
            content=TEXT(stored=True),
            date_indexed=DATETIME(stored=True, sortable=True),
            ai_tags=TEXT(stored=True),
            ai_summary=TEXT(stored=True),
        )
        self.ix = self._open_index()

    def _open_index(self):
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)
            return whoosh_index.create_in(self.index_dir, self.schema)
        if whoosh_index.exists_in(self.index_dir):
            return whoosh_index.open_dir(self.index_dir)
        return whoosh_index.create_in(self.index_dir, self.schema)

    @staticmethod
    def parse_search_query(search_text: str) -> Tuple[str, List[str], List[str]]:
        parts = search_text.strip().lower().split()
        keywords = []
        file_types = []
        for part in parts:
            if part.startswith(".") and len(part) > 1:
                file_types.append(part)
            elif part:
                keywords.append(part)
        whoosh_query_str = " ".join([f"{k}*" for k in keywords])
        return whoosh_query_str, keywords, file_types

    def perform_search(
        self,
        search_text: str,
        excluded_file_types: Set[str],
        path_filter: Optional[str] = None,
        selected_tags: Optional[Set[str]] = None,
    ) -> List[IndexedFile]:
        session = get_session()
        try:
            whoosh_query_str, keywords, file_types = self.parse_search_query(search_text)
            query = select(IndexedFile).where(not_(IndexedFile.file_type.in_(excluded_file_types)))

            if selected_tags:
                tag_filters = [IndexedFile.ai_tags.like(f"%{tag}%") for tag in selected_tags]
                query = query.where(or_(*tag_filters))

            if not whoosh_query_str and not file_types and not selected_tags:
                if len(search_text) > 0:
                    return []
                if path_filter:
                    if not path_filter.endswith("/"):
                        path_filter += "/"
                    query = query.where(IndexedFile.file_path.like(f"{path_filter}%"))
                query = query.order_by(desc(IndexedFile.date_indexed)).limit(100)
                return session.scalars(query).all()

            search_paths = None
            if whoosh_query_str:
                with self.ix.searcher() as searcher:
                    field_boosts = {
                        "file_name": 3.0,
                        "ai_summary": 2.0,
                        "ai_tags": 2.0,
                        "content": 1.0,
                    }
                    parser = MultifieldParser(field_boosts.keys(), schema=self.schema, fieldboosts=field_boosts)
                    parser.add_plugin(WildcardPlugin())
                    keyword_q = parser.parse(whoosh_query_str)
                    filter_q = None
                    if path_filter:
                        if not path_filter.endswith("/"):
                            path_filter += "/"
                        filter_q = Prefix("file_path", path_filter)
                    final_query = And([keyword_q, filter_q]) if filter_q else keyword_q
                    results = searcher.search(final_query, limit=500)
                    search_paths = [hit["file_path"] for hit in results]
                    if not search_paths:
                        return []

                query = query.where(IndexedFile.file_path.in_(search_paths))
            else:
                if path_filter:
                    if not path_filter.endswith("/"):
                        path_filter += "/"
                    query = query.where(IndexedFile.file_path.like(f"{path_filter}%"))

            if file_types:
                query = query.where(IndexedFile.file_type.in_(file_types))

            if search_paths:
                sql_results = session.scalars(query).all()
                results_map = {file.file_path: file for file in sql_results}
                ordered_results = [results_map[path] for path in search_paths if path in results_map]
                return ordered_results[:100]

            query = query.order_by(desc(IndexedFile.date_indexed)).limit(100)
            return session.scalars(query).all()

        except Exception as e:
            print("Error during search:", e)
            return []
        finally:
            session.close()

    def get_file_preview(self, file_path: str) -> Union[IndexedFile, None]:
        session = get_session()
        try:
            file_record = session.query(IndexedFile).filter_by(file_path=file_path).first()
            if not file_record:
                return None
            with self.ix.searcher() as searcher:
                hit = searcher.document(file_path=file_path)
                if hit:
                    file_record.extracted_content = hit.get("content", "")
                else:
                    file_record.extracted_content = "--- Preview not available (file not in search index) ---"
            return file_record
        except Exception as e:
            print("Error loading preview:", e)
            return None
        finally:
            session.close()

    @staticmethod
    def get_all_file_types() -> List[str]:
        session = get_session()
        try:
            query = (
                select(IndexedFile.file_type)
                .distinct()
                .where(not_(IndexedFile.file_type.like("unsupported%")))
                .order_by(IndexedFile.file_type)
            )
            return session.scalars(query).all()
        except Exception as e:
            print("Error getting file types:", e)
            return []
        finally:
            session.close()

    @staticmethod
    def get_all_types_for_exclusion() -> List[str]:
        session = get_session()
        try:
            return session.scalars(select(IndexedFile.file_type).distinct()).all()
        except Exception as e:
            print("Error unchecking all filters:", e)
            return []
        finally:
            session.close()

    @staticmethod
    def get_all_tags() -> List[str]:
        session = get_session()
        try:
            query = select(IndexedFile.ai_tags).distinct()
            results = [t for t in session.scalars(query).all() if t]
            tags = set()
            for entry in results:
                for tag in entry.split(","):
                    cleaned = tag.strip()
                    if cleaned:
                        tags.add(cleaned)
            return sorted(tags)
        except Exception as e:
            print("Error fetching tags:", e)
            return []
        finally:
            session.close()
