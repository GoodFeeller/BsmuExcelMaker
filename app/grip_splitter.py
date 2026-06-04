from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QSplitter, QSplitterHandle


class GripSplitterHandle(QSplitterHandle):
    GRIP_SYMBOL = "⋮"

    def __init__(self, orientation: Qt.Orientation, parent: QSplitter) -> None:
        super().__init__(orientation, parent)
        self._hovered = False
        self.setMouseTracking(True)
        self.setCursor(Qt.SplitHCursor if orientation == Qt.Horizontal else Qt.SplitVCursor)

    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self._hovered:
            painter.fillRect(self.rect(), QColor("#2563eb"))
            painter.setPen(QColor("#ffffff"))
        else:
            painter.fillRect(self.rect(), QColor("#cbd5e1"))
            painter.setPen(QColor("#475569"))

        painter.drawText(self.rect(), Qt.AlignCenter, self.GRIP_SYMBOL)
        painter.end()


class GripSplitter(QSplitter):
    def createHandle(self) -> QSplitterHandle:
        return GripSplitterHandle(self.orientation(), self)
