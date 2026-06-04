from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QStyledItemDelegate

from app.table_delegate import TopAlignedItemDelegate

TIME_BORDER_AFTER_ROLE = Qt.ItemDataRole.UserRole + 1
GROUP_BORDER_AFTER_ROLE = Qt.ItemDataRole.UserRole + 2

TIME_BORDER_COLOR = QColor("#94a3b8")
GROUP_BORDER_COLOR = QColor("#0f172a")
TIME_BORDER_WIDTH = 1
GROUP_BORDER_WIDTH = 3

# Совместимость с прежним именем роли
BORDER_AFTER_ROLE = TIME_BORDER_AFTER_ROLE


class AggregationItemDelegate(TopAlignedItemDelegate):
    """Границы: тонкие между блоками времени, жирные между группами."""

    def paint(self, painter, option, index) -> None:
        super().paint(painter, option, index)

        group_border = bool(index.data(GROUP_BORDER_AFTER_ROLE))
        time_border = bool(index.data(TIME_BORDER_AFTER_ROLE))

        if not group_border and not time_border:
            return

        painter.save()
        if group_border:
            painter.setPen(QPen(GROUP_BORDER_COLOR, GROUP_BORDER_WIDTH))
        else:
            painter.setPen(QPen(TIME_BORDER_COLOR, TIME_BORDER_WIDTH))

        rect = option.rect
        y = rect.bottom() - 1
        painter.drawLine(rect.left(), y, rect.right(), y)
        painter.restore()
