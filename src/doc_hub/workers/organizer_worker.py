import os
import shutil
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot
from src.doc_hub.core.ai_service import AIService
from src.doc_hub.core.file_processing import extract_content_from_file


class OrganizerWorker(QObject):
    analysis_progress = Signal(str)
    analysis_result = Signal(str, str, str)  # file_path, file_name, ai_category
    analysis_finished = Signal(str)

    organization_progress = Signal(str)
    organization_finished = Signal(str)

    def __init__(self, ai_service: AIService):
        super().__init__()
        self.ai_service = ai_service

    @Slot(str)
    def run_analysis(self, source_dir: str):
        self.analysis_progress.emit(f"Analyzing files in {source_dir}...")
        try:
            source_path = Path(source_dir)

            for entry in os.scandir(source_path):
                if entry.is_file():
                    file_path = Path(entry.path)
                    file_name = file_path.name

                    self.analysis_progress.emit(f"Analyzing: {file_name}")

                    display_type, content = extract_content_from_file(file_path)

                    ai_category = self.ai_service.get_file_category(file_name, content)

                    self.analysis_result.emit(str(file_path), file_name, ai_category)

            self.analysis_finished.emit("Analysis complete. Please review the suggestions.")
        except Exception as e:
            self.analysis_finished.emit(f"Error during analysis: {e}")

    @Slot(str, str, list)
    def run_organization(self, source_dir: str, dest_dir: str, files_to_move: list):
        self.organization_progress.emit("Starting organization...")
        try:
            dest_path = Path(dest_dir)
            moved_count = 0

            for file_path_str, category in files_to_move:
                try:
                    file_path = Path(file_path_str)

                    category_dir = dest_path / category
                    category_dir.mkdir(parents=True, exist_ok=True)

                    new_file_path = category_dir / file_path.name

                    shutil.move(file_path, new_file_path)

                    self.organization_progress.emit(f"MOVED: {file_path.name} -> {category}/")
                    moved_count += 1

                except Exception as e:
                    self.organization_progress.emit(f"ERROR moving {file_path_str}: {e}")

            self.organization_finished.emit(
                f"Organization complete. Moved {moved_count} files. You can undo this action (Right-click → Undo).")
        except Exception as e:
            self.organization_finished.emit(f"Error during organization: {e}")
