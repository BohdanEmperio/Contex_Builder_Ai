import os
import sys
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from ui.styles import DARK_STYLESHEET
from ui.main_window import MainWindow


def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def main():
    app = QApplication(sys.argv)
    icon_file = resource_path("icon.ico")
    if os.path.isfile(icon_file):
        app.setWindowIcon(QIcon(icon_file))
    app.setStyleSheet(DARK_STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()