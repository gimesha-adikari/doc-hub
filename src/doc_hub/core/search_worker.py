from __future__ import annotations
from PySide6.QtCore import QObject, Signal, Slot
from doc_hub.core.search_service import SearchService

class SearchWorker(QObject):
    results_ready = Signal(list)
    search_complete = Signal(str)

    def __init__(self, search_service: SearchService):
        super().__init__()
        self.search_service = search_service
        self.selected_tags = set()

    @Slot(str, set, str)
    def run_search(self, search_texts: str, excluded_file_types: set, path_filter: str | None):
        try:
            results = self.search_service.perform_search(
                search_texts,
                excluded_file_types,
                path_filter,
                self.selected_tags
            )
            self.results_ready.emit(results)
            message = f"{len(results)} results found." if results else "No results found."
            self.search_complete.emit(message)
        except Exception as e:
            print(f"Error during background search: {e}")
            self.search_complete.emit(f"Search error: {e}")
