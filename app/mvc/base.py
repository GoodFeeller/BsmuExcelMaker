from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMainWindow, QWidget


class ModelBase(QObject):
    """Базовая модель MVC-модуля."""


class ViewBase(QWidget):
    """Базовое представление MVC-модуля."""


class ControllerBase(QObject):
    """Базовый контроллер: связывает модель и представление."""

    def __init__(self, parent_window: QMainWindow) -> None:
        super().__init__(parent_window)
        self._parent_window = parent_window

    @property
    def parent_window(self) -> QMainWindow:
        return self._parent_window
