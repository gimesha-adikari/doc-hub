import sys
from PySide6.QtWidgets import QApplication

from src.app.main_window import MainWindow

if __name__ == "__main__":

    app = QApplication(sys.argv)

    try:
        with open("resources/style.qss", "r") as f:
            _style = f.read()
            app.setStyleSheet(_style)
    except FileNotFoundError:
        print("Stylesheet 'resources/style.qss' not found.")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())