from PySide6.QtCore import QUrl, QPoint
from PySide6.QtGui import QColor, QIcon, QDesktopServices, QAction, QPixmap, Qt
from PySide6.QtWidgets import QMainWindow, QGraphicsDropShadowEffect, QWidget, QHeaderView, QTableWidgetItem, QMenu

from src.app.settings_window import SettingsWindow
from src.ui.main_window_ui import Ui_MainWindow
from src.core.syntax_highlighter import Highlighter
from src.core.search_service import SearchService
from src.core.background_manager import BackgroundManager  # <-- NEW
from src.core.file_indexer import IMAGE_TYPES

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.search_service = SearchService()
        self.highlighter = Highlighter(self.ui.file_preview_text.document())

        self.manager = BackgroundManager(self.ui.statusbar, self)

        self.excluded_file_types = set()

        self.ui.search_splitter.setSizes([800, 200])
        self.ui.results_table.verticalHeader().setVisible(True)
        self.setup_table_columns()
        self.setup_icons_and_shadows()

        self.ui.settings_button.clicked.connect(self.open_settings_window)
        self.ui.filter_button.clicked.connect(self.show_filter_menu)
        self.ui.search_bar.textChanged.connect(self.on_search_text_changed)
        self.ui.results_table.itemSelectionChanged.connect(self.show_file_preview)
        self.ui.results_table.itemDoubleClicked.connect(self.open_file)

        self.manager.scan_finished.connect(self.on_scan_finished)

        self.manager.run_full_scan()
        self.on_search_text_changed()

    def setup_table_columns(self):
        header = self.ui.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

    def setup_icons_and_shadows(self):
        self.ui.settings_button.setText("")
        self.ui.settings_button.setIcon(QIcon("resources/icons/settings.svg"))
        self.ui.settings_button.setFixedSize(36, 36)
        self.ui.filter_button.setText("")
        self.ui.filter_button.setIcon(QIcon("resources/icons/filter.svg"))
        self.ui.filter_button.setFixedSize(36, 36)
        self.apply_shadow(self.ui.search_bar)
        self.apply_shadow(self.ui.settings_button)
        self.apply_shadow(self.ui.filter_button)
        self.apply_shadow(self.ui.organizer_target_path_input)
        self.apply_shadow(self.ui.organizer_browse_button)
        self.apply_shadow(self.ui.run_organizer_button)

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

    def show_filter_menu(self):
        file_types = self.search_service.get_all_file_types()
        menu = QMenu(self)

        show_all_action = QAction("Show all", self)
        show_all_action.triggered.connect(self.check_all_filters)
        menu.addAction(show_all_action)

        hide_all_action = QAction("Hide all", self)
        hide_all_action.triggered.connect(self.uncheck_all_filters)
        menu.addAction(hide_all_action)
        menu.addSeparator()

        if not file_types:
            no_types_action = QAction("No file types indexed yet", self)
            no_types_action.setEnabled(False)
            menu.addAction(no_types_action)

        for ftype in file_types:
            action = QAction(ftype, self)
            action.setCheckable(True)
            action.setChecked(ftype not in self.excluded_file_types)
            action.toggled.connect(
                lambda checked, typ=ftype: self.on_filter_toggled(checked, typ)
            )
            menu.addAction(action)

        menu.exec(self.ui.filter_button.mapToGlobal(QPoint(0, self.ui.filter_button.height())))

    def on_filter_toggled(self, checked: bool, file_type: str):
        if checked:
            self.excluded_file_types.discard(file_type)
        else:
            self.excluded_file_types.add(file_type)
        self.on_search_text_changed()

    def check_all_filters(self):
        self.excluded_file_types.clear()
        self.on_search_text_changed()

    def uncheck_all_filters(self):
        all_types = self.search_service.get_all_types_for_exclusion()
        self.excluded_file_types.update(all_types)
        self.on_search_text_changed()

    def on_search_text_changed(self):
        search_text = self.ui.search_bar.text()

        _, keywords, _ = self.search_service.parse_search_query(search_text)
        self.highlighter.set_search_terms(keywords)

        results = self.search_service.perform_search(search_text, self.excluded_file_types)

        self.ui.results_table.setRowCount(0)
        self.ui.results_table.setRowCount(len(results))
        for row, file in enumerate(results):
            file_size_str = self.format_size(file.file_size)
            mod_time_str = file.date_modified.strftime("%Y-%m-%d %H:%M")

            name_item = QTableWidgetItem(file.file_name)
            name_item.setData(0x0100, file.file_path)
            name_item.setData(0x0101, file.file_type)
            type_item = QTableWidgetItem(file.file_type)
            size_item = QTableWidgetItem(file_size_str)
            modified_item = QTableWidgetItem(mod_time_str)

            self.ui.results_table.setItem(row, 0, name_item)
            self.ui.results_table.setItem(row, 1, type_item)
            self.ui.results_table.setItem(row, 2, size_item)
            self.ui.results_table.setItem(row, 3, modified_item)

    def show_file_preview(self):
        selected_items = self.ui.results_table.selectedItems()
        if not selected_items:
            self.ui.preview_stack.setCurrentWidget(self.ui.page_default)
            return

        name_item = self.ui.results_table.item(self.ui.results_table.currentRow(), 0)
        if not name_item:
            return

        file_path = name_item.data(0x0100)
        file_type = name_item.data(0x0101)

        if not file_path:
            return

        if file_type =="image":
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
                self.highlighter.set_language(file_record.file_path)
                self.ui.file_preview_text.setText(file_record.extracted_content)
            else:
                self.highlighter.set_language(None)
                self.ui.file_preview_text.setText("--- Preview not available or file is empty ---")
            self.ui.preview_stack.setCurrentWidget(self.ui.page_text)

    def open_file(self, item: QTableWidgetItem):
        name_item = self.ui.results_table.item(item.row(), 0)
        file_path = name_item.data(0x0100)
        if file_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def on_scan_finished(self):
        self.ui.settings_button.setEnabled(True)
        self.ui.filter_button.setEnabled(True)
        self.on_search_text_changed()

    def run_full_scan(self):
        self.ui.settings_button.setEnabled(False)
        self.ui.filter_button.setEnabled(False)
        self.manager.run_full_scan()

    def update_watcher_paths(self):
        self.manager.update_watcher_paths()

    def request_scan(self):
        self.manager.request_scan()