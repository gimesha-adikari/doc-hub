from PySide6.QtCore import QUrl, QPoint, QDir
from PySide6.QtGui import QColor, QIcon, QDesktopServices, QAction, QPixmap, Qt
from PySide6.QtWidgets import QMainWindow, QGraphicsDropShadowEffect, QWidget, QHeaderView, QTableWidgetItem, QMenu, \
    QFileSystemModel

from src.app.settings_window import SettingsWindow
from src.ui.main_window_ui import Ui_MainWindow
from src.core.syntax_highlighter import Highlighter
from src.core.search_service import SearchService
from src.core.background_manager import BackgroundManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.search_service = SearchService()
        self.highlighter = Highlighter(self.ui.file_preview_text.document())

        self.manager = BackgroundManager(self.ui.statusbar, self)

        self.excluded_file_types = set()

        self.file_system_model = QFileSystemModel()
        self.file_system_model.setRootPath(QDir.homePath())
        self.file_system_model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)

        self.ui.explorer_tree_view.setModel(self.file_system_model)
        self.ui.explorer_tree_view.setRootIndex(self.file_system_model.index(QDir.homePath()))

        self.ui.explorer_tree_view.setColumnHidden(1, True)
        self.ui.explorer_tree_view.setColumnHidden(2, True)
        self.ui.explorer_tree_view.setColumnHidden(3, True)

        self.ui.search_splitter.setSizes([800, 200])
        self.ui.results_table.verticalHeader().setVisible(False)
        self.setup_table_columns()
        self.setup_icons_and_shadows()

        self.ui.settings_button.clicked.connect(self.open_settings_window)
        self.ui.filter_button.clicked.connect(self.show_filter_menu)
        self.ui.search_bar.textChanged.connect(self.on_search_text_changed)

        self.ui.results_table.itemSelectionChanged.connect(self.show_preview_from_table)
        self.ui.results_table.itemDoubleClicked.connect(self.open_file_from_table)
        self.ui.explorer_tree_view.selectionModel().selectionChanged.connect(self.show_preview_from_tree)
        self.ui.explorer_tree_view.doubleClicked.connect(self.open_file_from_tree)

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

        if not search_text:
            self.ui.view_stack.setCurrentWidget(self.ui.page_explorer)
            self.highlighter.set_search_terms([])
            self.show_preview_from_tree()
        else:
            self.ui.view_stack.setCurrentWidget(self.ui.page_search_results)

            current_index = self.ui.explorer_tree_view.currentIndex()
            current_path = self.file_system_model.filePath(current_index)

            if not current_path or not QDir(current_path).exists():
                current_path = QDir.homePath()

            _, keywords, _ = self.search_service.parse_search_query(search_text)
            self.highlighter.set_search_terms(keywords)

            results = self.search_service.perform_search(search_text, self.excluded_file_types, path_filter=current_path)

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

    def show_preview_from_table(self):
        selected_items = self.ui.results_table.selectedItems()
        if not selected_items:
            self.ui.preview_stack.setCurrentWidget(self.ui.page_default)
            return

        name_item = self.ui.results_table.item(self.ui.results_table.currentRow(), 0)
        if not name_item:
            return

        file_path = name_item.data(0x0100)
        file_type = name_item.data(0x0101)
        self.update_preview_pane(file_path, file_type)

    def show_preview_from_tree(self):
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
                self.highlighter.set_language(file_record.file_path)
                self.ui.file_preview_text.setText(file_record.extracted_content)
            else:
                self.highlighter.set_language(None)
                self.ui.file_preview_text.setText("--- Preview not available or file is empty ---")
            self.ui.preview_stack.setCurrentWidget(self.ui.page_text)

    def open_file_from_table(self,item: QTableWidgetItem):
        name_item = self.ui.results_table.item(item.row, 0)
        file_path = name_item.data(0x0100)
        if file_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def open_file_from_tree(self, index):
        if not self.file_system_model.isDir(index):
            file_path = self.file_system_model.filePath(index)
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
