from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QLabel
from PySide6.QtCore import Qt, Signal, QPoint

class TagPickerDialog(QWidget):
    tags_selected = Signal(set)

    def __init__(self, all_tags: list[str], selected_tags: set[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filter by Tags")
        self.setMinimumSize(420, 500)
        self.all_tags = all_tags or []
        self.selected_tags = set(selected_tags or set())

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

        search_label = QLabel("Search tags:")
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_tags)

        layout.addWidget(search_label)
        layout.addWidget(self.search_input)

        self.tag_list = QListWidget()
        self.tag_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.tag_list, 1)

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

        self.populate_tags()
        self.tag_list.itemSelectionChanged.connect(self.emit_selection)

        if parent is not None:
            geom = parent.geometry()
            x = geom.right() - 440
            y = geom.top() + 100
            self.move(QPoint(x, y))

    def populate_tags(self):
        self.tag_list.clear()
        for tag in sorted(self.all_tags):
            item = QListWidgetItem(tag)
            if tag in self.selected_tags:
                item.setSelected(True)
            self.tag_list.addItem(item)

    def filter_tags(self, text):
        text = (text or "").lower()
        for i in range(self.tag_list.count()):
            item = self.tag_list.item(i)
            item.setHidden(text not in item.text().lower())

    def select_all(self):
        for i in range(self.tag_list.count()):
            self.tag_list.item(i).setSelected(True)

    def clear_all(self):
        for i in range(self.tag_list.count()):
            self.tag_list.item(i).setSelected(False)

    def emit_selection(self):
        selected = {self.tag_list.item(i).text()
                    for i in range(self.tag_list.count())
                    if self.tag_list.item(i).isSelected()}
        self.tags_selected.emit(selected)
