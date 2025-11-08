from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QLabel
from PySide6.QtCore import Qt, Signal, QPoint

class TypePickerDialog(QWidget):
    types_selected = Signal(set)

    def __init__(self, all_types: list[str], excluded_types: set[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filter by File Types")
        self.setMinimumSize(420, 500)
        self.all_types = all_types or []
        self.excluded_types = set(excluded_types or set())

        self.setStyleSheet("""
            QWidget {
                background-color: #1e1f22;
                color: #e6e6e6;
                font-family: 'JetBrains Mono', 'Ubuntu Mono', monospace;
                font-size: 13px;
            }
            QLineEdit {
                background-color: #2b2d31;
                border: 1px solid #3a3b3c;
                border-radius: 6px;
                padding: 6px 10px;
                color: #e6e6e6;
            }
            QPushButton {
                background-color: #2f80ed;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #1f6fe0; }
            QListWidget {
                background-color: #25272b;
                border: 1px solid #3a3b3c;
                border-radius: 6px;
                padding: 4px;
            }
            QListWidget::item { padding: 6px; }
            QListWidget::item:selected {
                background-color: #2f80ed;
                color: white;
            }
        """)

        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setFixedWidth(420)
        self.setWindowModality(Qt.NonModal)

        layout = QVBoxLayout(self)

        search_label = QLabel("Search file types:")
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_types)

        layout.addWidget(search_label)
        layout.addWidget(self.search_input)

        self.type_list = QListWidget()
        self.type_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.type_list, 1)

        button_row = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        clear_all_btn = QPushButton("Clear All")
        close_btn = QPushButton("Close")

        select_all_btn.clicked.connect(self.select_all)
        clear_all_btn.clicked.connect(self.clear_all)
        close_btn.clicked.connect(self.close)

        button_row.addWidget(select_all_btn)
        button_row.addWidget(clear_all_btn)
        button_row.addStretch(1)
        button_row.addWidget(close_btn)
        layout.addLayout(button_row)

        self.populate_types()
        self.type_list.itemSelectionChanged.connect(self.emit_selection)

        if parent is not None:
            geom = parent.geometry()
            x = geom.right() - 440
            y = geom.top() + 100
            self.move(QPoint(x, y))

    def populate_types(self):
        self.type_list.clear()
        for file_type in sorted(self.all_types):
            item = QListWidgetItem(file_type)
            if file_type not in self.excluded_types:
                item.setSelected(True)
            self.type_list.addItem(item)

    def filter_types(self, text):
        text = (text or "").lower()
        for i in range(self.type_list.count()):
            item = self.type_list.item(i)
            item.setHidden(text not in item.text().lower())

    def select_all(self):
        for i in range(self.type_list.count()):
            self.type_list.item(i).setSelected(True)

    def clear_all(self):
        for i in range(self.type_list.count()):
            self.type_list.item(i).setSelected(False)

    def emit_selection(self):
        selected = {self.type_list.item(i).text()
                    for i in range(self.type_list.count())
                    if self.type_list.item(i).isSelected()}
        excluded = set(self.all_types) - selected
        self.types_selected.emit(excluded)
