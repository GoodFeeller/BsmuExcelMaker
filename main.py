import sys

from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from app.app_paths import icon_path
from app.shell.main_window import MainWindow
from app.styles import APP_STYLESHEET


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("RCPCST Sheduler")
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(APP_STYLESHEET)

    icon_file = icon_path()
    if icon_file.exists():
        app_icon = QIcon(str(icon_file))
        app.setWindowIcon(app_icon)

    window = MainWindow()
    if icon_file.exists():
        window.setWindowIcon(app_icon)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
