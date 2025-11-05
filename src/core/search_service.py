from sqlalchemy import select, desc, text, column, Integer, table, not_
from src.core.database import get_session, IndexedFile


class SearchService:
    def __init__(self):
        pass

    def parse_search_query(self, search_text: str) -> (str, list[str], list[str]):
        parts = search_text.strip().lower().split()
        keywords = []
        file_types = []

        for part in parts:
            if part.startswith(".") and len(part) > 1:
                file_types.append(part)
            else:
                keywords.append(part)

        fts_query = " ".join([f'"{k}*"' for k in keywords])
        return fts_query, keywords, file_types

    def perform_search(self, search_text: str, excluded_file_types: set) -> list[IndexedFile]:
        fts_query, keywords, file_types = self.parse_search_query(search_text)

        session = get_session()
        try:
            query = select(IndexedFile).where(
                not_(IndexedFile.file_type.in_(excluded_file_types))
            )

            if not fts_query and not file_types:
                if len(search_text) > 0:
                    return []
                query = query.order_by(desc(IndexedFile.date_indexed))
            else:
                if fts_query:
                    fts_table = table(
                        "indexed_file_fts",
                        column("rowid", Integer),
                        column("file_name"),
                        column("extracted_content"),
                    )
                    query = query.join(
                        fts_table,
                        IndexedFile.id == fts_table.c.rowid
                    ).where(
                        text("indexed_file_fts MATCH :query")
                    ).params(
                        query=fts_query
                    ).order_by(
                        desc(text("rank"))
                    )

                if file_types:
                    query = query.where(IndexedFile.file_type.in_(file_types))

                if not fts_query and file_types:
                    query = query.order_by(desc(IndexedFile.date_indexed))

            query = query.limit(100)
            results = session.scalars(query).all()
            return results

        except Exception as e:
            print(f"Error during search: {e}")
            return []
        finally:
            session.close()

    def get_file_preview(self, file_path: str) -> IndexedFile | None:
        session = get_session()
        try:
            return session.query(IndexedFile).filter_by(file_path=file_path).first()
        except Exception as e:
            print(f"Error loading preview: {e}")
            return None
        finally:
            session.close()

    def get_all_file_types(self) -> list[str]:
        session = get_session()
        try:
            query = (
                select(IndexedFile.file_type)
                .distinct()
                .where(not_(IndexedFile.file_type.like("unsupported (%)")))
                .order_by(IndexedFile.file_type)
            )
            return session.scalars(query).all()
        except Exception as e:
            print(f"Error getting file types: {e}")
            return []
        finally:
            session.close()

    def get_all_types_for_exclusion(self) -> list[str]:
        session = get_session()
        try:
            return session.scalars(select(IndexedFile.file_type).distinct()).all()
        except Exception as e:
            print(f"Error unchecking all filters: {e}")
            return []
        finally:
            session.close()