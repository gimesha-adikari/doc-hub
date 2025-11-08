import sys
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from doc_hub.app.main_window import MainWindow

from doc_hub.core.resource_utils import resource_path


def main():
    app = QApplication(sys.argv)

    qss_path = resource_path("style.qss")

    try:
        with open(qss_path, "r", encoding="utf-8") as f:
            _style = f.read()
            app.setStyleSheet(_style)
            app.setFont(QFont("Inter", 10))
    except FileNotFoundError:
        print("⚠️ Stylesheet 'resources/style.qss' not found — using default style.")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
