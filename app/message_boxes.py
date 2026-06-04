from PySide6.QtWidgets import QMessageBox, QStyle, QWidget


def show_success(parent: QWidget | None, title: str, text: str) -> None:
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    style = box.style()
    if style is not None:
        icon = style.standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        box.setIconPixmap(icon.pixmap(48, 48))
    else:
        box.setIcon(QMessageBox.Icon.Information)
    box.exec()
