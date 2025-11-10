import json
import re
import shutil
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Optional

import markdown
import pyperclip
from PySide6.QtCore import QUrl, QPoint, QDir, QFileSystemWatcher, QTimer, QThread, Signal, Slot, QPropertyAnimation, \
    QEasingCurve
from PySide6.QtGui import QColor, QIcon, QDesktopServices, QAction, QPixmap, QTextCursor, Qt, QCursor, QFont
from PySide6.QtWidgets import (QMainWindow, QGraphicsDropShadowEffect, QWidget,
                               QHeaderView, QTableWidgetItem, QMenu,
                               QFileSystemModel, QFileIconProvider, QFileDialog, QCheckBox, QHBoxLayout,
                               QAbstractItemView, QPushButton, QMessageBox, QDialog, QVBoxLayout, QListWidget,
                               QScrollArea, QGridLayout, QLabel, QTextEdit, QTableWidget, QStatusBar, QComboBox)

from offline_ai.auto_launcher import launch_local_model
from src.doc_hub.workers.duplicate_worker import DuplicateWorker
from src.doc_hub.workers.index_worker import IndexWorker
from src.doc_hub.app.settings_window import SettingsWindow
from src.doc_hub.app.tag_picker_dialog import TagPickerDialog
from src.doc_hub.app.type_picker_dialog import TypePickerDialog
from src.doc_hub.core.ai_service import AIService
from src.doc_hub.workers.ai_worker import AIWorker
from src.doc_hub.core.background_manager import BackgroundManager
from src.doc_hub.workers.organizer_worker import OrganizerWorker
from src.doc_hub.core.search_service import SearchService
from src.doc_hub.workers.search_worker import SearchWorker
from src.doc_hub.core.syntax_highlighter import Highlighter
from src.doc_hub.ui.main_window_ui import Ui_MainWindow
from src.doc_hub.core.resource_utils import resource_path

TREE_SITTER_LIB = "build/my-languages.so"

TS_LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".rs": "rust",
    ".go": "go",
    ".php": "php",
    ".rb": "ruby",
    ".cs": "c_sharp",
    ".swift": "swift",
    ".kt": "kotlin",
    ".kts": "kotlin",
}

class MainWindow(QMainWindow):
    search_requested = Signal(str, set, str)
    ai_question_requested = Signal(str, str)

    analysis_requested = Signal(str)
    organization_requested = Signal(str, str, list)

    def __init__(self):
        super().__init__()
        self._initialized = False
        self._is_populating = None
        self.undo_log_pending = None
        self.dot_count = None
        self.typing_timer = None
        self.index_thread = None
        self.duplicate_thread = None
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        #--
        self.model_selector = QComboBox()
        self.model_selector.addItems(["Gemini", "Mistral", "Phi-2"])
        self.model_selector.currentTextChanged.connect(self.on_model_selected)

        self.model_selector.setToolTip("Select AI model for chat (Gemini / Mistral / Phi-2).")
        self.model_selector.setFixedWidth(110)
        try:
            self.ui.search_bar_layout.addWidget(self.model_selector)
        except Exception:
            self.ui.left_vertical_layout.addWidget(self.model_selector)
        #--

        self.search_service = SearchService()
        self.highlighter = Highlighter(self.ui.file_preview_text.document())
        self.manager = BackgroundManager(self.ui.statusbar, self)

        self.ai_service = AIService()

        default_model = "Mistral"
        launch_local_model(default_model)

        self.excluded_file_types = set()
        self.selected_tags = set()

        self.current_tag_count = 0
        self.current_type_count = 0
        self.refresh_filter_counts()

        self.file_system_model = QFileSystemModel()
        self.file_system_model.setIconProvider(QFileIconProvider())
        self.file_system_model.setRootPath(QDir.homePath())

        self.file_system_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot | QDir.NoSymLinks)

        self.ui.explorer_tree_view.setModel(self.file_system_model)
        self.ui.explorer_tree_view.setRootIndex(self.file_system_model.index(QDir.homePath()))

        self.ui.explorer_tree_view.setHeaderHidden(False)
        self.ui.explorer_tree_view.setColumnWidth(0, 250)

        self.ui.results_table.verticalHeader().setVisible(False)
        self.setup_table_columns()

        self.ui.search_bar.setPlaceholderText("🔍  Search documents, AI tags, or content...")
        self.ui.view_toggle_button = QPushButton("🗂 Grid View", self.ui.tab_smart_search)
        self.ui.search_bar_layout.addWidget(self.ui.view_toggle_button)
        self.ui.view_toggle_button.setCheckable(True)
        self.ui.view_toggle_button.toggled.connect(self.toggle_view_mode)

        self.ui.ai_insights_button = QPushButton("📊 Insights", self.ui.tab_smart_search)
        self.ui.search_bar_layout.addWidget(self.ui.ai_insights_button)
        self.ui.ai_insights_button.clicked.connect(self.generate_search_insights)

        index_menu = self.menuBar().addMenu("Index")
        reindex_action = QAction("Rebuild Index", self)
        reindex_action.triggered.connect(self.trigger_reindex)
        index_menu.addAction(reindex_action)

        tools_menu = self.menuBar().addMenu("Tools")
        dup_action = QAction("Find Duplicates", self)
        dup_action.triggered.connect(self.trigger_find_duplicates)
        tools_menu.addAction(dup_action)

        self.setStatusBar(self.statusBar() if self.statusBar() else QStatusBar())

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)

        self.search_thread = QThread()
        self.search_worker = SearchWorker(self.search_service)
        self.search_worker.moveToThread(self.search_thread)

        self.search_timer.timeout.connect(self.trigger_search)
        self.ui.search_bar.textChanged.connect(self.search_timer.start)
        self.ui.explorer_tree_view.selectionModel().selectionChanged.connect(self.search_timer.start)

        self.search_requested.connect(self.search_worker.run_search)
        self.search_worker.results_ready.connect(self.on_search_results_ready)
        self.search_worker.search_complete.connect(self.ui.statusbar.showMessage)
        self.search_thread.start()

        self.ai_thread = QThread()
        self.ai_worker = AIWorker(self.ai_service)
        self.ai_worker.moveToThread(self.ai_thread)
        self.ai_question_requested.connect(self.ai_worker.get_ai_response)
        self.ai_worker.response_ready.connect(self.on_ai_response_ready)
        self.ai_worker.ai_error.connect(self.on_ai_error)
        self.ai_thread.start()

        self.organizer_thread = QThread()
        self.organizer_worker = OrganizerWorker(self.ai_service)
        self.organizer_worker.moveToThread(self.organizer_thread)

        self.analysis_requested.connect(self.organizer_worker.run_analysis)
        self.organization_requested.connect(self.organizer_worker.run_organization)

        self.organizer_worker.analysis_progress.connect(self.ui.statusbar.showMessage)
        self.organizer_worker.analysis_result.connect(self.add_organizer_table_item)
        self.organizer_worker.analysis_finished.connect(self.on_analysis_finished)

        self.organizer_worker.organization_progress.connect(self.ui.statusbar.showMessage)
        self.organizer_worker.organization_finished.connect(self.on_organization_finished)

        self.ui.organizer_undo_button = QPushButton("↩️  Undo Last Move", self.ui.tab_file_organizer)
        self.ui.file_organizer_layout.addWidget(self.ui.organizer_undo_button)
        self.ui.organizer_undo_button.setObjectName("organizer_undo_button")

        self.ui.organizer_history_button = QPushButton("📜 View Undo History", self.ui.tab_file_organizer)
        self.ui.file_organizer_layout.addWidget(self.ui.organizer_history_button)
        self.ui.organizer_history_button.setObjectName("organizer_history_button")
        self.ui.organizer_history_button.clicked.connect(self.open_undo_history)

        self.organizer_thread.start()

        self.results_card_container = QScrollArea(self.ui.tab_smart_search)
        self.results_card_container.setWidgetResizable(True)
        self.results_card_container.setVisible(False)
        self.results_card_container.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.results_card_container.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.results_card_container.setStyleSheet("""
            QScrollArea {
                background-color: #1e1f22;
                border: none;
            }
        """)

        self.results_card_widget = QWidget()
        self.results_card_layout = QGridLayout(self.results_card_widget)
        self.results_card_layout.setContentsMargins(16, 12, 16, 12)
        self.results_card_layout.setSpacing(14)
        self.results_card_container.setWidget(self.results_card_widget)

        self.ui.left_vertical_layout.insertWidget(1, self.results_card_container)

        self._last_card_width = None

        self.ui.settings_button.clicked.connect(self.open_settings_window)
        self.ui.filter_button.clicked.connect(self.show_filter_menu)

        self.ui.ai_ask_button.clicked.connect(self.on_ai_ask_clicked)
        self.ui.ai_question_input.returnPressed.connect(self.on_ai_ask_clicked)

        self.ui.results_table.itemSelectionChanged.connect(self.update_preview_from_selection)
        self.ui.results_table.itemDoubleClicked.connect(self.open_file_from_table)
        self.ui.explorer_tree_view.selectionModel().selectionChanged.connect(self.update_preview_from_selection)
        self.ui.explorer_tree_view.doubleClicked.connect(self.open_file_from_tree)

        self.ui.results_table.itemSelectionChanged.connect(self.clear_ai_chat)
        self.ui.explorer_tree_view.selectionModel().selectionChanged.connect(self.clear_ai_chat)

        self.ui.results_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.results_table.customContextMenuRequested.connect(self.show_table_context_menu)

        self.ui.organizer_source_browse_button.clicked.connect(self.select_organizer_source)
        self.ui.organizer_dest_browse_button.clicked.connect(self.select_organizer_dest)
        self.ui.organizer_analyze_button.clicked.connect(self.start_analysis)
        self.ui.organizer_run_button.clicked.connect(self.start_organization)
        self.ui.organizer_undo_button.clicked.connect(self.undo_last_organization)

        self.undo_log_path = Path("database/last_organizer_log.json")
        self.ui.organizer_table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
        )
        header = self.ui.organizer_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.ui.organizer_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        undo_action = QAction("Undo Last Move", self)
        undo_action.triggered.connect(self.undo_last_organization)
        undo_action.setShortcut("Ctrl+Z")
        self.ui.main_tab_widget.addAction(undo_action)
        self.ui.main_tab_widget.setContextMenuPolicy(Qt.ActionsContextMenu)

        self.manager.scan_finished.connect(self.on_scan_finished)
        self.manager.scan_finished.connect(self.refresh_filter_counts)

        self.setup_icons_and_shadows()

        self.manager.run_full_scan()
        self.trigger_search()

        self.watcher = QFileSystemWatcher()
        self.watcher.fileChanged.connect(self.on_files_changed)

        self.results_card_container.resizeEvent = self._on_card_container_resized
        try:
            self.ai_service.model_choice = self.model_selector.currentText()
        except Exception:
            pass

        self._initialized = True

    def infer_ts_lang(self, file_path: Optional[str]) -> Optional[str]:
        if not file_path:
            return None
        try:
            ext = Path(file_path).suffix.lower()
            return TS_LANG_MAP.get(ext)
        except Exception:
            return None

    def _on_card_container_resized(self, event):
        try:
            if not getattr(self, "_initialized", False):
                return super(QScrollArea, self.results_card_container).resizeEvent(event)

            new_width = self.results_card_container.viewport().width()
            if getattr(self, "_last_card_width", None) != new_width:
                self._last_card_width = new_width
                QTimer.singleShot(200, self.populate_card_view)

        except Exception as e:
            print(f"Resize event skipped: {e}")

        return super(QScrollArea, self.results_card_container).resizeEvent(event)

    def setup_table_columns(self):
        header = self.ui.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

    def setup_icons_and_shadows(self):
        self.ui.settings_button.setText("")
        self.ui.settings_button.setIcon(QIcon(resource_path("icons", "settings.svg")))
        self.ui.settings_button.setFixedSize(36, 36)
        self.ui.filter_button.setText("")
        self.ui.filter_button.setIcon(QIcon(resource_path("icons", "filter.svg")))
        self.ui.filter_button.setFixedSize(36, 36)
        self.ui.explorer_tree_view.setStyleSheet("""
        QTreeView {
                background-color: #2f2f2f;
                color: #e4e6eb;
                border: none;
                font-family: "JetBrains Mono", "Ubuntu", sans-serif;
            }
            QTreeView::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QTreeView::item:hover {
                background-color: #3a3b3c;
            }
            QHeaderView::section {
                background-color: #3a3b3c;
                color: #e4e6eb;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #444;
                font-weight: bold;
            }
        """)

        self.ui.results_table.setStyleSheet("""
        QTableWidget {
            background-color: #1e1f22;
            alternate-background-color: #242529;
            color: #e4e6eb;
            border: none;
            gridline-color: #303134;
            font-family: 'JetBrains Mono', 'Ubuntu Mono', monospace;
            font-size: 13px;
            selection-background-color: #2f80ed;
            selection-color: white;
        }
        QHeaderView::section {
            background-color: #2a2b2f;
            color: #cccccc;
            padding: 6px;
            border: none;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
        }
        QTableCornerButton::section {
            background-color: #2a2b2f;
            border: none;
        }
        """)

        self.ui.file_preview_text.setStyleSheet("""
        QTextEdit {
            background-color: #1c1d21;
            border: 1px solid #2f3034;
            color: #e4e6eb;
            border-radius: 8px;
            padding: 10px;
            font-family: 'JetBrains Mono', 'Ubuntu Mono', monospace;
            font-size: 13px;
        }
        """)

        self.ui.search_bar.setStyleSheet("""
        QLineEdit {
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 20px;
            padding: 8px 16px;
            color: #ffffff;
            font-size: 14px;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }
        QLineEdit:focus {
            border: 1px solid #2f80ed;
            background-color: rgba(255, 255, 255, 0.12);
        }
        """)

        self.ui.ai_chat_area.setStyleSheet("""
        QTextBrowser {
            background-color: #16171a;
            border: 1px solid #2a2b2f;
            border-radius: 8px;
            padding: 8px;
            color: #d8dadf;
            font-size: 13px;
        }
        """)

        self.ui.ai_question_input.setStyleSheet("""
        QLineEdit {
            background-color: #2b2d31;
            border: 1px solid #3a3b3c;
            border-radius: 14px;
            padding: 6px 12px;
            color: #e6e6e6;
            font-size: 13px;
        }
        QLineEdit:focus {
            border: 1px solid #2f80ed;
            background-color: #2c2f35;
        }
        """)

        button_style = """
        QPushButton {
            background-color: rgba(255, 255, 255, 0.07);
            color: #e6e6e6;
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 10px;
            padding: 6px 14px;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            font-size: 13px;
        }
        QPushButton:hover {
            background-color: rgba(47,128,237,0.25);
            border-color: #2f80ed;
        }
        QPushButton:checked {
            background-color: #2f80ed;
            color: white;
        }
        """
        self.ui.view_toggle_button.setStyleSheet(button_style)
        self.ui.ai_insights_button.setStyleSheet(button_style)

        self.apply_shadow(self.ui.search_bar)
        self.apply_shadow(self.ui.settings_button)
        self.apply_shadow(self.ui.filter_button)
        self.apply_shadow(self.ui.ai_question_input)
        self.apply_shadow(self.ui.ai_ask_button)

    def open_settings_window(self):
        settings_dialog = SettingsWindow(self)
        settings_dialog.finished.connect(self.on_settings_close)
        settings_dialog.exec()

    def on_settings_close(self):
        self.manager.update_watcher_paths()
        self.manager.run_full_scan()

    def apply_shadow(self, widget: QWidget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 4)
        widget.setGraphicsEffect(shadow)

    def format_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / 1024 ** 2:.1f} MB"
        else:
            return f"{size_bytes / 1024 ** 3:.1f} GB"

    def toggle_view_mode(self, checked):
        if checked:
            self.ui.view_toggle_button.setText("📋 List View")
            self.ui.explorer_tree_view.setVisible(False)
            self.ui.results_table.setVisible(False)
            self.results_card_container.setVisible(True)
            self.populate_card_view()
        else:
            self.ui.view_toggle_button.setText("🗂 Grid View")
            self.ui.explorer_tree_view.setVisible(True)
            self.results_card_container.setVisible(False)
            self.ui.results_table.setVisible(True)

    def show_table_context_menu(self, pos):
        row = self.ui.results_table.currentRow()
        if row < 0:
            return
        name_item = self.ui.results_table.item(row, 0)
        if not name_item:
            return
        file_path = name_item.data(0x0100)
        global_pos = self.ui.results_table.viewport().mapToGlobal(pos)
        self.show_card_context_menu(file_path)

    def on_card_clicked(self, file_path: str):
        if not file_path:
            return
        file_record = self.search_service.get_file_preview(file_path)
        file_type = file_record.file_type if file_record else "unsupported"
        self.update_preview_pane(file_path, file_type)

        for r in range(self.ui.results_table.rowCount()):
            item = self.ui.results_table.item(r, 0)
            if item and item.data(0x0100) == file_path:
                self.ui.results_table.selectRow(r)
                return

    def show_card_context_menu(self, file_path: str):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1f22;
                color: #e6e6e6;
                border: 1px solid #3a3b3c;
                padding: 6px;
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: #2f80ed;
                color: white;
            }
        """)

        open_action = QAction("📂  Open File", self)
        reveal_action = QAction("📁  Show in Folder", self)
        copy_action = QAction("📋  Copy Path", self)
        ai_summary_action = QAction("🧠  Open with AI Summary", self)

        open_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(file_path)))
        reveal_action.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(file_path).parent))))
        try:
            copy_action.triggered.connect(lambda: pyperclip.copy(file_path))
        except Exception:
            copy_action.triggered.connect(lambda: print(file_path))

        ai_summary_action.triggered.connect(lambda: self.show_ai_summary_popup(file_path))

        menu.addAction(open_action)
        menu.addAction(reveal_action)
        menu.addSeparator()
        menu.addAction(ai_summary_action)
        menu.addAction(copy_action)

        menu.exec(QCursor.pos())

    def show_ai_summary_popup(self, file_path: str):

        record = self.search_service.get_file_preview(file_path)
        file_name = Path(file_path).name
        summary = getattr(record, "ai_summary", None)
        raw_tags = getattr(record, "ai_tags", "")
        tags = []
        if raw_tags:
            try:
                tags = json.loads(raw_tags) if raw_tags.strip().startswith("[") else [t.strip() for t in
                                                                                      raw_tags.split(",")]
            except Exception:
                tags = [t.strip() for t in raw_tags.split(",")]

        content_preview = textwrap.shorten(record.extracted_content or "", width=400, placeholder="...")

        dlg = QDialog(self)
        dlg.setWindowTitle(f"AI Summary — {file_name}")
        dlg.setMinimumWidth(550)
        dlg.setStyleSheet("""
            QDialog {
                background-color: #1c1d21;
                border: 1px solid #2a2b2f;
                border-radius: 10px;
            }
            QLabel {
                color: #e6e6e6;
                font-size: 13px;
            }
            QPushButton {
                background-color: #2f80ed;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1f6fe0;
            }
            QTextEdit {
                background-color: #242529;
                color: #d8dadf;
                border: 1px solid #2a2b2f;
                border-radius: 8px;
                padding: 6px;
                font-family: "JetBrains Mono", monospace;
                font-size: 13px;
            }
        """)

        layout = QVBoxLayout(dlg)
        title = QLabel(f"📄 <b>{file_name}</b>")
        title.setFont(QFont("Inter", 12, QFont.Bold))
        layout.addWidget(title)

        summary_label = QLabel("<b>🧠 AI Summary:</b>")
        layout.addWidget(summary_label)

        summary_box = QTextEdit()
        summary_box.setReadOnly(True)
        summary_box.setText(summary or "No AI summary available.")
        layout.addWidget(summary_box)

        if tags:
            tag_label = QLabel(f"<b>🏷️ Tags:</b>  {'   '.join(tags)}")
            tag_label.setStyleSheet("color: #b0b0b0; font-size: 12px; margin-top: 5px;")
            layout.addWidget(tag_label)

        preview_label = QLabel("<b>📜 Content Snippet:</b>")
        layout.addWidget(preview_label)

        preview_box = QTextEdit()
        preview_box.setReadOnly(True)
        preview_box.setText(content_preview)
        layout.addWidget(preview_box)

        button_row = QHBoxLayout()
        open_btn = QPushButton("📂 Open File")
        ai_btn = QPushButton("🔄 Reanalyze with AI")
        chat_btn = QPushButton("💬 Chat with AI")
        close_btn = QPushButton("Close")

        button_row.addWidget(open_btn)
        button_row.addWidget(ai_btn)
        button_row.addWidget(chat_btn)
        button_row.addWidget(close_btn)
        layout.addLayout(button_row)

        open_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(file_path)))

        def reanalyze_and_update():
            try:
                self.ai_service.model_choice = self.model_selector.currentText()
                tags_str, summary_text = self.ai_service.get_tags_and_summary(record.extracted_content or "")
                summary_box.setPlainText(summary_text or "No AI summary available.")
                if tags_str:
                    nonlocal_tag_label = None
                    for i in range(layout.count()):
                        w = layout.itemAt(i).widget()
                        if isinstance(w, QLabel) and w.text().startswith("<b>🏷️ Tags:</b>"):
                            nonlocal_tag_label = w
                            break
                    if nonlocal_tag_label:
                        nonlocal_tag_label.setText(f"<b>🏷️ Tags:</b>  {tags_str}")
                    else:
                        new_tag_label = QLabel(f"<b>🏷️ Tags:</b>  {tags_str}")
                        new_tag_label.setStyleSheet("color: #b0b0b0; font-size: 12px; margin-top: 5px;")
                        layout.insertWidget(3, new_tag_label)  # insert below summary
                self.ui.statusbar.showMessage("File reanalyzed successfully.", 3000)
            except Exception as e:
                self.ui.statusbar.showMessage(f"AI reanalysis failed: {e}", 5000)

        ai_btn.clicked.connect(reanalyze_and_update)

        close_btn.clicked.connect(dlg.close)

        def start_chat_with_document():
            self.ai_service.model_choice = self.model_selector.currentText()

            self.ui.preview_tab_widget.setCurrentWidget(self.ui.tab_ai_chat)
            if record and record.extracted_content:
                self.ui.file_preview_text.setText(record.extracted_content)
                self.ui.ai_chat_area.clear()
                self.ui.ai_question_input.setFocus()
                self.ui.ai_chat_area.append(
                    f"<div style='opacity:0.6;'>💬 Chat started for <b>{file_name}</b></div>"
                )
            dlg.close()

        chat_btn.clicked.connect(start_chat_with_document)

        dlg.setWindowOpacity(0)
        anim = QPropertyAnimation(dlg, b"windowOpacity")
        anim.setDuration(200)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.start(QPropertyAnimation.DeleteWhenStopped)

        dlg.setLayout(layout)
        dlg.exec()

    def update_tag_chips(self):
        for i in reversed(range(self.ui.tag_chip_layout.count())):
            chip = self.ui.tag_chip_layout.itemAt(i).widget()
            if chip:
                chip.deleteLater()

        for tag in self.selected_tags:
            chip = QPushButton(f"🏷 {tag}")
            chip.setStyleSheet("""
                QPushButton {
                    background-color: #2f80ed;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 2px 8px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #1f6fe0;
                }
            """)
            chip.clicked.connect(lambda _, t=tag: self.remove_tag_chip(t))
            self.ui.tag_chip_layout.addWidget(chip)

    def remove_tag_chip(self, tag):
        self.selected_tags.discard(tag)
        self.update_tag_chips()
        self.trigger_search()

    def show_filter_menu(self):
        file_types = self.search_service.get_all_file_types()
        all_tags = self.search_service.get_all_tags()
        type_count = len(file_types)
        tag_count = len(all_tags)

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1f22;
                color: #e6e6e6;
                border: 1px solid #3a3b3c;
                padding: 6px;
                font-family: 'JetBrains Mono', 'Ubuntu Mono', monospace;
                font-size: 13px;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: #2f80ed;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background-color: #444;
                margin: 6px 10px;
            }
        """)

        show_all_action = QAction("Show all", self)
        show_all_action.triggered.connect(self.check_all_filters)
        menu.addAction(show_all_action)

        hide_all_action = QAction("Hide all", self)
        hide_all_action.triggered.connect(self.uncheck_all_filters)
        menu.addAction(hide_all_action)
        menu.addSeparator()

        type_label = f"📄  Filter by Types ({type_count})"
        tag_label = f"🏷️  Filter by Tags ({tag_count})"

        type_picker_action = QAction(type_label, self)
        tag_picker_action = QAction(tag_label, self)

        type_picker_action.triggered.connect(self.open_type_picker)
        tag_picker_action.triggered.connect(self.open_tag_picker)

        menu.addAction(type_picker_action)
        menu.addAction(tag_picker_action)

        menu.exec(self.ui.filter_button.mapToGlobal(QPoint(0, self.ui.filter_button.height())))

    def populate_card_view(self):
        if getattr(self, "_is_populating", False):
            return
        self._is_populating = True

        current_index = self.ui.explorer_tree_view.currentIndex()
        current_path = self.file_system_model.filePath(current_index)
        if current_path and not self.file_system_model.isDir(current_index):
            current_path = str(Path(current_path).parent)
        if not current_path or not QDir(current_path).exists():
            current_path = self.file_system_model.rootPath()

        new_width = self.results_card_container.viewport().width()
        layout_empty = (self.results_card_layout.count() == 0)
        if (not layout_empty) and getattr(self, "_last_card_width", None) == new_width:
            self._is_populating = False
            return

        self._last_card_width = new_width

        from PySide6.QtWidgets import (
            QLabel, QFrame, QVBoxLayout
        )

        while self.results_card_layout.count():
            child = self.results_card_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        try:
            results = self.search_service.perform_search(
                self.ui.search_bar.text(),
                self.excluded_file_types,
                getattr(self.search_worker, "selected_tags", self.selected_tags),
                current_path
            )
        except TypeError:
            results = self.search_service.perform_search(
                self.ui.search_bar.text(),
                self.excluded_file_types
            )

        if not results:
            label = QLabel("No results found.")
            label.setStyleSheet("color: #888; font-size: 14px;")
            self.results_card_layout.addWidget(label, 0, 0)
            self._is_populating = False
            return

        scroll_width = self.results_card_container.viewport().width()
        card_width = 300
        card_spacing = self.results_card_layout.spacing()
        col_count = max(1, scroll_width // (card_width + card_spacing))

        row, col = 0, 0

        for file in results:
            card = QFrame()
            card.setObjectName("file_card")
            card.setStyleSheet("""
                QFrame#file_card {
                    background-color: #1f2023;
                    border: 1px solid #2a2b2f;
                    border-radius: 10px;
                    padding: 10px;
                }
                QFrame#file_card:hover {
                    border: 1px solid #2f80ed;
                    background-color: #242529;
                }
                QLabel {
                    color: #e4e6eb;
                    font-size: 12px;
                }
            """)

            layout = QVBoxLayout(card)
            layout.setSpacing(4)

            title = QLabel(f"📄 <b>{file.file_name}</b>")
            title.setTextFormat(Qt.RichText)

            summary = QLabel(file.ai_summary or "No AI summary available.")
            summary.setWordWrap(True)
            summary.setStyleSheet("color:#b0b0b0; font-size:11px;")

            details = QLabel(
                f"Type: {file.file_type}\n"
                f"Size: {self.format_size(file.file_size)}\n"
                f"Modified: {file.date_modified.strftime('%Y-%m-%d %H:%M')}"
            )
            details.setStyleSheet("color:#9a9da0; font-size:11px;")

            layout.addWidget(title)
            layout.addWidget(details)
            layout.addWidget(summary)

            card.mousePressEvent = (lambda fp=file.file_path, ft=file.file_type:
                                    (lambda e: self.update_preview_pane(fp, ft)))()

            self.results_card_layout.addWidget(card, row, col)
            col += 1
            if col >= col_count:
                col = 0
                row += 1

            anim = QPropertyAnimation(card, b"windowOpacity")
            anim.setDuration(150)
            anim.setStartValue(0)
            anim.setEndValue(1)
            anim.start(QPropertyAnimation.DeleteWhenStopped)

        self.results_card_layout.setAlignment(Qt.AlignTop)
        self.results_card_container.verticalScrollBar().setSingleStep(40)

        self._is_populating = False

    def populate_cards_from_results(self, results: list):

        from PySide6.QtWidgets import (
            QLabel, QFrame, QVBoxLayout
        )
        if getattr(self, "_is_populating", False):
            return
        self._is_populating = True

        while self.results_card_layout.count():
            child = self.results_card_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not results:
            from PySide6.QtWidgets import QLabel
            label = QLabel("No results found.")
            label.setStyleSheet("color: #888; font-size: 14px;")
            self.results_card_layout.addWidget(label, 0, 0)
            self._is_populating = False
            return

        scroll_width = self.results_card_container.viewport().width()
        card_width = 300
        card_spacing = self.results_card_layout.spacing()
        col_count = max(1, scroll_width // (card_width + card_spacing))

        row, col = 0, 0

        for file in results:
            card = QFrame()
            card.setObjectName("file_card")
            card.setStyleSheet("""
                QFrame#file_card {
                    background-color: #1f2023;
                    border: 1px solid #2a2b2f;
                    border-radius: 10px;
                    padding: 10px;
                }
                QFrame#file_card:hover {
                    border: 1px solid #2f80ed;
                    background-color: #242529;
                }
                QLabel {
                    color: #e4e6eb;
                    font-size: 12px;
                }
            """)

            layout = QVBoxLayout(card)
            layout.setSpacing(4)

            title = QLabel(f"📄 <b>{file.file_name}</b>")
            title.setTextFormat(Qt.RichText)

            summary = QLabel(file.ai_summary or "No AI summary available.")
            summary.setWordWrap(True)
            summary.setStyleSheet("color:#b0b0b0; font-size:11px;")

            details = QLabel(
                f"Type: {file.file_type}\n"
                f"Size: {self.format_size(file.file_size)}\n"
                f"Modified: {file.date_modified.strftime('%Y-%m-%d %H:%M')}"
            )
            details.setStyleSheet("color:#9a9da0; font-size:11px;")

            layout.addWidget(title)
            layout.addWidget(details)
            layout.addWidget(summary)

            def make_onclick(fp, ft):
                return lambda e: self.update_preview_pane(fp, ft)

            card.mousePressEvent = make_onclick(file.file_path, file.file_type)

            self.results_card_layout.addWidget(card, row, col)
            col += 1
            if col >= col_count:
                col = 0
                row += 1

            anim = QPropertyAnimation(card, b"windowOpacity")
            anim.setDuration(150)
            anim.setStartValue(0)
            anim.setEndValue(1)
            anim.start(QPropertyAnimation.DeleteWhenStopped)

        self.results_card_layout.setAlignment(Qt.AlignTop)
        self.results_card_container.verticalScrollBar().setSingleStep(40)
        self._is_populating = False

    def generate_search_insights(self):
        results = self.search_service.perform_search(
            self.ui.search_bar.text(),
            self.excluded_file_types
        )
        all_text = " ".join([r.extracted_content or "" for r in results])
        summary, tags = self.ai_service.get_tags_and_summary(all_text)
        QMessageBox.information(self, "AI Insights",
                                f"<b>Summary:</b> {summary}<br><br><b>Top Tags:</b> {tags}")

    def open_tag_picker(self):
        all_tags = self.search_service.get_all_tags()
        dialog = TagPickerDialog(all_tags, self.selected_tags, self)
        dialog.tags_selected.connect(self.on_tags_selected)
        dialog.show()
        try:
            self.slide_in_widget(dialog)
        except Exception:
            pass

    def open_type_picker(self):
        all_types = self.search_service.get_all_file_types()
        dialog = TypePickerDialog(all_types, self.excluded_file_types, self)
        dialog.types_selected.connect(self.on_types_selected)
        dialog.show()
        try:
            self.slide_in_widget(dialog)
        except Exception:
            pass

    def slide_in_widget(self, widget):
        start_pos = widget.pos() + QPoint(420, 0)
        end_pos = widget.pos()
        anim = QPropertyAnimation(widget, b"pos", widget)
        anim.setDuration(250)
        anim.setStartValue(start_pos)
        anim.setEndValue(end_pos)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start(QPropertyAnimation.DeleteWhenStopped)

    def on_types_selected(self, excluded_types: set[str]):
        self.excluded_file_types = excluded_types
        self.trigger_search()

    def on_tags_selected(self, selected_tags: set[str]):
        self.selected_tags = selected_tags
        self.trigger_search()

    def refresh_filter_counts(self):
        all_tags = self.search_service.get_all_tags()
        all_types = self.search_service.get_all_file_types()
        self.current_tag_count = len(all_tags)
        self.current_type_count = len(all_types)
        self.ui.filter_button.setToolTip(
            f"{self.current_type_count} file types and {self.current_tag_count} AI tags available."
        )

    def on_filter_toggled(self, checked: bool, file_type: str):
        if checked:
            self.excluded_file_types.discard(file_type)
        else:
            self.excluded_file_types.add(file_type)
        self.trigger_search()

    def on_tag_toggled(self, checked: bool, tag: str):
        if checked:
            self.selected_tags.add(tag)
        else:
            self.selected_tags.discard(tag)
        self.trigger_search()

    def check_all_filters(self):
        self.excluded_file_types.clear()
        self.selected_tags.clear()
        self.trigger_search()

    def uncheck_all_filters(self):
        all_types = self.search_service.get_all_types_for_exclusion()
        self.excluded_file_types.update(all_types)
        self.selected_tags.clear()
        self.trigger_search()

    @Slot()
    def trigger_search(self):
        self.ui.statusbar.showMessage("Searching...")
        search_text = self.ui.search_bar.text()

        current_index = self.ui.explorer_tree_view.currentIndex()
        current_path = self.file_system_model.filePath(current_index)

        if current_path and not self.file_system_model.isDir(current_index):
            current_path = str(Path(current_path).parent)

        if not current_path or not QDir(current_path).exists():
            current_path = self.file_system_model.rootPath()

        if search_text:
            _, keywords, _ = self.search_service.parse_search_query(search_text)
            self.highlighter.set_search_terms(keywords)
        else:
            self.highlighter.set_search_terms([])

        self.search_worker.selected_tags = self.selected_tags
        self.search_requested.emit(search_text, self.excluded_file_types, current_path)

    @Slot(list)
    def on_search_results_ready(self, results: list):
        # update list/table as before
        self.ui.results_table.setRowCount(0)
        self.ui.results_table.setRowCount(len(results))

        for row, file in enumerate(results):
            file_size_str = self.format_size(file.file_size)
            mod_time_str = file.date_modified.strftime("%Y-%m-%d %H:%M")
            name_item = QTableWidgetItem(file.file_name)
            name_item.setData(0x0100, file.file_path)
            name_item.setData(0x0101, file.file_type)
            type_item = QTableWidgetItem(file.file_type)
            badge = file.file_type.upper().replace('.', '')
            type_item.setText(f"● {badge}")

            size_item = QTableWidgetItem(file_size_str)
            modified_item = QTableWidgetItem(mod_time_str)
            self.ui.results_table.setItem(row, 0, name_item)
            self.ui.results_table.setItem(row, 1, type_item)
            self.ui.results_table.setItem(row, 2, size_item)
            self.ui.results_table.setItem(row, 3, modified_item)

            icon = QIcon.fromTheme("text-x-generic")
            if file.file_type.lower().startswith(".pdf"):
                icon = QIcon.fromTheme("application-pdf")
            elif "image" in file.file_type.lower():
                icon = QIcon.fromTheme("image-x-generic")
            elif file.file_type.lower() in [".txt", ".md"]:
                icon = QIcon.fromTheme("text-plain")
            elif file.file_type.lower() in [".py", ".java", ".js"]:
                icon = QIcon.fromTheme("text-x-script")

            name_item = self.ui.results_table.item(row, 0)
            name_item.setIcon(icon)
            self.ui.results_table.setRowHeight(row, 28)

        try:
            if getattr(self, "results_card_container", None) and self.results_card_container.isVisible():
                self.populate_cards_from_results(results)
        except Exception as e:
            print(f"Failed to update card view: {e}")

    def show_result_table(self):
        if hasattr(self, 'results_card_container'):
            self.results_card_container.hide()
        self.ui.results_table.show()
        self.ui.view_toggle_button.setText("🗂 Grid View")

    def update_preview_from_selection(self):
        file_path = None
        file_type = None

        sender = self.sender()
        if sender == self.ui.results_table:
            selected_items = self.ui.results_table.selectedItems()
            if not selected_items:
                self.ui.preview_stack.setCurrentWidget(self.ui.page_default)
                return
            name_item = self.ui.results_table.item(self.ui.results_table.currentRow(), 0)
            if not name_item:
                return
            file_path = name_item.data(0x0100)
            file_type = name_item.data(0x0101)

        else:
            current_index = self.ui.explorer_tree_view.currentIndex()
            if not current_index.isValid() or self.file_system_model.isDir(current_index):
                self.ui.preview_stack.setCurrentWidget(self.ui.page_default)
                return

            file_path = self.file_system_model.filePath(current_index)
            file_record = self.search_service.get_file_preview(file_path)
            file_type = file_record.file_type if file_record else "unsupported"

        self.update_preview_pane(file_path, file_type)

    def update_preview_pane(self, file_path: str | None, file_type: str | None):
        if not file_path:
            self.ui.preview_stack.setCurrentWidget(self.ui.page_default)
            return

        self.ui.preview_tab_widget.setCurrentWidget(self.ui.tab_preview)

        has_text_content = False

        if file_type == "image":
            self.highlighter.set_language(None)
            pixmap = QPixmap(file_path)
            scaled_pixmap = pixmap.scaled(
                self.ui.image_preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.ui.image_preview_label.setPixmap(scaled_pixmap)
            self.ui.preview_stack.setCurrentWidget(self.ui.page_image)

        elif file_type.startswith("unsupported"):
            self.highlighter.set_language(None)
            self.ui.preview_stack.setCurrentWidget(self.ui.page_default)


        else:

            file_record = self.search_service.get_file_preview(file_path)

            if file_record and file_record.extracted_content:

                self.highlighter.set_language(
                    file_record.file_path,
                    ts_lang=self.infer_ts_lang(file_record.file_path)
                )

                if file_record.ai_summary:

                    summary_html = f"""

                    <div style='background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #22252a, stop:1 #1d1f23);

                                border: 1px solid #2a2b2f;

                                border-radius: 8px;

                                padding: 8px 10px;

                                margin-bottom: 10px;

                                color: #cfd1d5;

                                font-size: 13px;

                                font-family: "Inter", sans-serif;'>

                        <b>🧠 AI Summary:</b><br>{file_record.ai_summary}

                    </div>

                    <pre style="font-family: 'JetBrains Mono', monospace;

                                font-size: 13px;

                                color: #e4e6eb;

                                white-space: pre-wrap;

                                line-height: 1.4;">{file_record.extracted_content}</pre>

                    """

                    self.ui.file_preview_text.setHtml(summary_html)

                else:

                    self.ui.file_preview_text.setText(file_record.extracted_content)

                has_text_content = True

            else:

                self.highlighter.set_language(None)

                self.ui.file_preview_text.setText("--- Preview not available or file is empty ---")

            self.ui.preview_stack.setCurrentWidget(self.ui.page_text)

        self.ui.preview_tab_widget.setTabEnabled(1, has_text_content)
        if not has_text_content:
            self.ui.ai_chat_area.setPlaceholderText("Select a file with text content to start chatting.")
        else:
            self.ui.ai_chat_area.setPlaceholderText("Ask a question about the document in the 'Preview' tab...")

    @Slot()
    def clear_ai_chat(self):
        self.ui.ai_chat_area.clear()

    @Slot()
    def on_ai_ask_clicked(self):
        user_question = self.ui.ai_question_input.text().strip()
        if not user_question:
            return

        document_content = self.ui.file_preview_text.toPlainText()

        if not document_content:
            self.on_ai_error("There is no document content to ask questions about.")
            return

        timestamp = datetime.now().strftime("%H:%M")

        user_html = f"""
        <div style="display: flex; justify-content: flex-end; margin: 6px 0;">
          <div style="background-color: #3a3b3c; color: #ffffff; padding: 10px 14px;
                      border-radius: 12px; max-width: 70%; font-size: 14px;
                      box-shadow: rgba(0,0,0,0.25) 0 2px 6px;">
            {user_question}
            <div style="font-size: 10px; opacity: 0.6; text-align: right; margin-top: 3px;">
                {datetime.now().strftime("%H:%M")}
            </div>
          </div>
        </div>
        """

        self.ai_service.model_choice = self.model_selector.currentText()

        self.ui.ai_chat_area.append(user_html)
        self.ui.ai_chat_area.verticalScrollBar().setValue(
            self.ui.ai_chat_area.verticalScrollBar().maximum()
        )

        self.ui.ai_question_input.clear()
        self.ui.ai_question_input.setEnabled(False)
        self.ui.ai_ask_button.setEnabled(False)
        self.ui.statusbar.showMessage("Asking AI...")

        self.ui.preview_tab_widget.setCurrentWidget(self.ui.tab_ai_chat)

        self.ui.ai_chat_area.append(
            '<div id="typing" style="color: rgba(255,255,255,0.4); font-style: italic;">AI is typing<span id="dots"></span></div>'
        )

        self.typing_timer = QTimer(self)
        self.dot_count = 0

        def animate_dots():
            self.dot_count = (self.dot_count + 1) % 4
            dots = "." * self.dot_count
            cursor = self.ui.ai_chat_area.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertHtml(f'<script>document.getElementById("dots").innerHTML="{dots}";</script>')

        self.typing_timer.timeout.connect(animate_dots)
        self.typing_timer.start(500)

        self.ai_question_requested.emit(document_content, user_question)

    @Slot(str, str)
    def on_ai_response_ready(self, question: str, answer: str):
        if hasattr(self, "typing_timer"):
            self.typing_timer.stop()

        # Remove the "AI is typing..." line
        cursor = self.ui.ai_chat_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()

        rendered_html = markdown.markdown(answer, extensions=['fenced_code', 'tables'])

        pre_style = (
            'background-color: transparent; '
            'color: #e8eaed; '
            'padding: 0; '
            'margin: 0; '
            'border-radius: 0; '
            'font-family: "JetBrains Mono", monospace; '
            'font-size: 13px; '
            'white-space: pre-wrap; '
            'word-wrap: break-word;'
        )

        code_style = (
            'background-color: rgba(255,255,255,0.08); '
            'color: #e8eaed; '
            'padding: 2px 4px; '
            'border-radius: 4px; '
            'font-family: "JetBrains Mono", monospace; '
            'font-size: 13px; '
            'white-space: pre-wrap; '
            'word-wrap: break-word;'
        )

        rendered_html = re.sub(r'<pre(.*?)>', f'<pre style="{pre_style}">', rendered_html)
        rendered_html = re.sub(r'<code(.*?)>', f'<code style="{code_style}">', rendered_html)
        timestamp = datetime.now().strftime("%H:%M")

        ai_html = f"""
        <div style="display: flex; justify-content: flex-start; margin: 6px 0;">
          <div style="background-color: #202123; color: #e8eaed; padding: 10px 14px;
                      border-radius: 12px; max-width: 75%; font-size: 14px;
                      box-shadow: rgba(0,0,0,0.3) 0 2px 8px;">
            {rendered_html}
            <div style="font-size: 10px; opacity: 0.6; text-align: right; margin-top: 3px;">
                {datetime.now().strftime("%H:%M")}
            </div>
          </div>
        </div>
        """

        self.ui.ai_chat_area.append(ai_html)
        self.ui.ai_chat_area.verticalScrollBar().setValue(
            self.ui.ai_chat_area.verticalScrollBar().maximum()
        )

        self.ui.ai_question_input.setEnabled(True)
        self.ui.ai_ask_button.setEnabled(True)
        self.ui.statusbar.showMessage("AI response received.", 3000)
        self.ui.ai_question_input.setFocus()

    @Slot(str)
    def on_ai_error(self, error_message: str):
        error_html = f"""
        <div style="text-align: center; margin: 5px;">
            <div style="background-color: #5a2a2a; color: white; display: inline-block; 
                        padding: 10px; border-radius: 10px; max-width: 80%; 
                        text-align: left; word-wrap: break-word;">
                <b>AI Error:</b> {error_message}
            </div>
        </div>
        """
        self.ui.ai_chat_area.append(error_html)

        self.ui.ai_question_input.setEnabled(True)
        self.ui.ai_ask_button.setEnabled(True)
        self.ui.statusbar.showMessage("An AI error occurred.", 3000)
        self.ui.ai_question_input.setFocus()

    def open_file_from_table(self, item: QTableWidgetItem):
        row = item.row()
        name_item = self.ui.results_table.item(row, 0)
        if name_item:
            file_path = name_item.data(0x0100)
            if file_path:
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def open_file_from_tree(self, index):
        if self.file_system_model.isDir(index):
            file_path = self.file_system_model.filePath(index)
            if file_path:
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    @Slot()
    def select_organizer_source(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder_path:
            self.ui.organizer_source_path_input.setText(folder_path)

    @Slot()
    def select_organizer_dest(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder_path:
            self.ui.organizer_dest_path_input.setText(folder_path)

    @Slot()
    def start_analysis(self):
        source_dir = self.ui.organizer_source_path_input.text()
        if not source_dir:
            self.ui.statusbar.showMessage("Please select a source folder first.")
            return

        self.ui.organizer_table.setRowCount(0)
        self.set_organizer_ui_enabled(False)
        self.analysis_requested.emit(source_dir)

    @Slot(str, str, str)
    def add_organizer_table_item(self, file_path, file_name, ai_category):
        row = self.ui.organizer_table.rowCount()
        self.ui.organizer_table.insertRow(row)

        checkbox = QCheckBox()
        checkbox.setChecked(True)
        checkbox_widget = QWidget()
        layout = QHBoxLayout(checkbox_widget)
        layout.addWidget(checkbox)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.ui.organizer_table.setCellWidget(row, 0, checkbox_widget)

        name_item = QTableWidgetItem(file_name)
        name_item.setData(Qt.UserRole, file_path)  # Store full path
        self.ui.organizer_table.setItem(row, 1, name_item)

        category_item = QTableWidgetItem(ai_category)
        self.ui.organizer_table.setItem(row, 2, category_item)

    @Slot(str)
    def on_analysis_finished(self, message):
        self.ui.statusbar.showMessage(message, 5000)
        self.set_organizer_ui_enabled(True)

    @Slot()
    def start_organization(self):
        source_dir = self.ui.organizer_source_path_input.text()
        dest_dir = self.ui.organizer_dest_path_input.text()

        if not source_dir or not dest_dir:
            self.ui.statusbar.showMessage("Please select source and destination folders.")
            return

        files_to_move = []
        for row in range(self.ui.organizer_table.rowCount()):
            checkbox = self.ui.organizer_table.cellWidget(row, 0).findChild(QCheckBox)
            if checkbox and checkbox.isChecked():
                file_path = self.ui.organizer_table.item(row, 1).data(Qt.UserRole)
                category = self.ui.organizer_table.item(row, 2).text().strip()
                files_to_move.append((file_path, category))

        if not files_to_move:
            self.ui.statusbar.showMessage("No files checked to organize.")
            return

        self.undo_log_pending = [(src, str(Path(dest_dir) / cat / Path(src).name))
                                 for src, cat in files_to_move]

        self.set_organizer_ui_enabled(False)
        self.organization_requested.emit(source_dir, dest_dir, files_to_move)

    @Slot(str)
    def on_organization_finished(self, message):
        self.ui.statusbar.showMessage(message, 5000)
        self.set_organizer_ui_enabled(True)

        if hasattr(self, "undo_log_pending"):
            self.log_organization(self.undo_log_pending)
            del self.undo_log_pending

        self.start_analysis()

    def set_organizer_ui_enabled(self, enabled: bool):
        self.ui.organizer_source_browse_button.setEnabled(enabled)
        self.ui.organizer_dest_browse_button.setEnabled(enabled)
        self.ui.organizer_analyze_button.setEnabled(enabled)
        self.ui.organizer_run_button.setEnabled(enabled)

    def log_organization(self, moves: list[tuple[str, str]]):
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "moves": [{"from": src, "to": dst} for src, dst in moves],
            }
            self.undo_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.undo_log_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            history_file = self.undo_log_path.parent / "organizer_history.json"
            history = []
            if history_file.exists():
                try:
                    history = json.load(open(history_file, "r", encoding="utf-8"))
                except Exception:
                    history = []

            data["moved"] = len(moves)
            history.append(data)

            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)

        except Exception as e:
            print(f"Failed to save undo history: {e}")

    @Slot()
    def undo_last_organization(self):
        from PySide6.QtWidgets import QMessageBox

        if not self.undo_log_path.exists():
            self.ui.statusbar.showMessage("No previous organization to undo.", 5000)
            return

        confirm = QMessageBox.question(
            self,
            "Undo Last Move",
            "Are you sure you want to undo the last organization?\n\n"
            "All moved files will be restored to their original locations.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if confirm != QMessageBox.StandardButton.Yes:
            self.ui.statusbar.showMessage("Undo canceled.", 3000)
            return

        try:
            with open(self.undo_log_path, "r", encoding="utf-8") as f:
                log = json.load(f)
            moves = log.get("moves", [])
            if not moves:
                self.ui.statusbar.showMessage("Undo log empty.", 5000)
                return

            restored = 0
            for move in moves:
                src = move["to"]
                dst = move["from"]
                src_path = Path(src)
                dst_path = Path(dst)
                if src_path.exists():
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(src_path, dst_path)
                    restored += 1

            self.ui.statusbar.showMessage(f"Undo complete. Restored {restored} files.", 5000)
            self.start_analysis()

            try:
                history_file = self.undo_log_path.parent / "organizer_history.json"
                if history_file.exists():
                    all_history = json.load(open(history_file, "r", encoding="utf-8"))
                    if all_history:
                        last_ts = all_history[-1].get("timestamp")
                        all_history = [
                            h for h in all_history if h.get("timestamp") != last_ts
                        ]
                        json.dump(all_history, open(history_file, "w", encoding="utf-8"), indent=2)
            except Exception as e:
                print(f"Failed to update history after undo: {e}")

        except Exception as e:
            self.ui.statusbar.showMessage(f"Undo failed: {e}", 7000)

    def open_undo_history(self):
        history_file = self.undo_log_path.parent / "organizer_history.json"
        if not history_file.exists():
            QMessageBox.information(self, "Undo History", "No history available yet.")
            return

        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Undo History", f"Failed to load history: {e}")
            return

        if not history:
            QMessageBox.information(self, "Undo History", "No sessions logged yet.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Undo History")
        layout = QVBoxLayout(dialog)

        list_widget = QListWidget(dialog)
        for entry in reversed(history):  # show newest first
            ts = entry.get("timestamp", "?")
            count = entry.get("moved", "?")
            list_widget.addItem(f"{ts} — {count} files moved")

        layout.addWidget(list_widget)

        button_layout = QVBoxLayout()
        view_button = QPushButton("🔍 View Details")
        undo_button = QPushButton("↩️ Undo Selected Session")
        close_button = QPushButton("Close")

        button_row = QHBoxLayout()
        button_row.addWidget(view_button)
        button_row.addWidget(undo_button)
        button_row.addWidget(close_button)
        layout.addLayout(button_row)

        def view_details():
            selected = list_widget.currentRow()
            if selected == -1:
                QMessageBox.warning(dialog, "Undo History", "Please select a session first.")
                return

            real_index = len(history) - 1 - selected  # reverse index
            session = history[real_index]
            moves = session.get("moves", [])

            detail_dialog = QDialog(dialog)
            detail_dialog.setWindowTitle(f"Session Details — {session.get('timestamp', '?')}")
            vbox = QVBoxLayout(detail_dialog)
            file_list = QListWidget(detail_dialog)

            for move in moves:
                src = move.get("from", "")
                dst = move.get("to", "")
                file_list.addItem(f"{Path(src).name}  →  {Path(dst).parent.name}/")

            vbox.addWidget(file_list)

            close_btn = QPushButton("Close")
            vbox.addWidget(close_btn)
            close_btn.clicked.connect(detail_dialog.close)

            detail_dialog.setLayout(vbox)
            detail_dialog.resize(700, 400)
            detail_dialog.exec()

        def undo_selected():
            selected = list_widget.currentRow()
            if selected == -1:
                QMessageBox.warning(dialog, "Undo History", "Please select a session first.")
                return

            real_index = len(history) - 1 - selected
            session = history[real_index]
            moves = session.get("moves", [])

            confirm = QMessageBox.question(
                dialog,
                "Undo Selected Session",
                f"Are you sure you want to undo {len(moves)} files from session "
                f"{session.get('timestamp', '?')}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return

            restored = 0
            for move in moves:
                src = move["to"]
                dst = move["from"]
                src_path = Path(src)
                dst_path = Path(dst)
                if src_path.exists():
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(src_path, dst_path)
                    restored += 1

            QMessageBox.information(
                dialog,
                "Undo Complete",
                f"Restored {restored} files from session {session.get('timestamp', '?')}."
            )

            try:
                history_file = self.undo_log_path.parent / "organizer_history.json"
                if history_file.exists():
                    all_history = json.load(open(history_file, "r", encoding="utf-8"))
                    all_history = [
                        h for h in all_history
                        if h.get("timestamp") != session.get("timestamp")
                    ]
                    json.dump(all_history, open(history_file, "w", encoding="utf-8"), indent=2)
            except Exception as e:
                print(f"Failed to remove undone session: {e}")

            dialog.close()
            self.start_analysis()

        view_button.clicked.connect(view_details)
        undo_button.clicked.connect(undo_selected)
        close_button.clicked.connect(dialog.close)

        dialog.setLayout(layout)
        dialog.resize(600, 450)
        dialog.exec()

    def on_scan_finished(self):
        self.ui.settings_button.setEnabled(True)
        self.ui.filter_button.setEnabled(True)
        self.trigger_search()

    def run_full_scan(self):
        self.ui.settings_button.setEnabled(False)
        self.ui.filter_button.setEnabled(False)
        self.manager.run_full_scan()

    def update_watcher_paths(self):
        self.manager.update_watcher_paths()

    def request_scan(self):
        self.manager.request_scan()

    def trigger_reindex(self):
        if self.index_thread and self.index_thread.isRunning():
            QMessageBox.warning(self, "Indexing", "Indexing is already running.")
            return

        selected_path = self.current_directory if hasattr(self, 'current_directory') else '.'
        self.index_thread = IndexWorker([selected_path], drop_removed=True)
        self.index_thread.progress.connect(lambda msg: self.statusBar().showMessage(msg))
        self.index_thread.finished.connect(self.on_index_finished)
        try:
            self.index_thread.start()
        except RuntimeError:
            QMessageBox.warning(self, "Thread Error", "Could not start reindex thread.")

    def on_index_finished(self, success, message):
        if success:
            self.statusBar().showMessage("Index updated successfully.")
            QMessageBox.information(self, "Indexing Complete", message)
        else:
            QMessageBox.critical(self, "Indexing Failed", message)

    def on_files_changed(self, changed_paths):
        if not self.index_thread or not self.index_thread.isRunning():
            self.index_thread = IndexWorker(changed_paths, drop_removed=False)
            self.index_thread.start()

    def trigger_find_duplicates(self):
        if self.duplicate_thread and self.duplicate_thread.isRunning():
            QMessageBox.warning(self, "Duplicate Scan", "A duplicate scan is already running.")
            return

        selected_path = getattr(self, "current_directory", ".")
        self.duplicate_thread = DuplicateWorker([selected_path])
        self.duplicate_thread.progress.connect(lambda msg: self.statusBar().showMessage(msg))
        self.duplicate_thread.finished.connect(self.on_duplicates_finished)
        try:
            self.duplicate_thread.start()
        except RuntimeError:
            QMessageBox.warning(self, "Thread Error", "Could not start duplicate scan thread.")

    def on_duplicates_finished(self, success, message, report_path):
        self.statusBar().showMessage(message)
        if not success:
            QMessageBox.critical(self, "Duplicate Scan Failed", message)
            return

        QMessageBox.information(self, "Duplicate Scan Complete", f"{message}\n\nReport: {report_path}")
        self.show_duplicate_results(report_path)

    def show_duplicate_results(self, report_path):
        try:
            report = json.loads(Path(report_path).read_text(encoding="utf-8"))
            duplicates = report.get("duplicate_groups", {})

            dialog = QDialog(self)
            dialog.setWindowTitle("Duplicate Files Report")
            layout = QVBoxLayout(dialog)
            layout.addWidget(QLabel(f"Generated at: {report.get('generated_at')}"))

            table = QTableWidget()
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels(["Hash", "File Path", "Size (KB)"])
            rows = sum(len(v) for v in duplicates.values())
            table.setRowCount(rows)

            r = 0
            for hash_val, files in duplicates.items():
                for f in files:
                    table.setItem(r, 0, QTableWidgetItem(hash_val[:12] + "…"))
                    table.setItem(r, 1, QTableWidgetItem(f["path"]))
                    table.setItem(r, 2, QTableWidgetItem(str(round(f["size"] / 1024, 2))))
                    r += 1

            table.resizeColumnsToContents()
            layout.addWidget(table)
            dialog.resize(900, 600)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load duplicate report:\n{e}")

    def closeEvent(self, event):
        print("Closing application... shutting down threads.")
        self.search_thread.quit()
        self.search_thread.wait()

        self.ai_thread.quit()
        self.ai_thread.wait()

        if self.manager.indexer_thread and self.manager.indexer_thread.isRunning():
            self.manager.indexer_thread.quit()
            self.manager.indexer_thread.wait()

        event.accept()

    @Slot(str)
    def on_model_selected(self, model_name: str):
        from src.doc_hub.offline_ai.auto_launcher import launch_local_model
        if model_name.lower() in ("mistral", "phi-2"):
            launch_local_model(model_name.lower())
