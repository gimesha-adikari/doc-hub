import sys
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from src.doc_hub.app.main_window import MainWindow

from core.resource_utils import resource_path
import warnings
import os

os.environ["QT_LOGGING_RULES"] = "qt.core.qobject.connectslotsbyname=false"
warnings.filterwarnings("ignore", category=UserWarning, module="tika")


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
