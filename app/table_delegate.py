from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStyledItemDelegate


class TopAlignedItemDelegate(QStyledItemDelegate):
    """Keep multiline cell text aligned to the top (Qt default centers it vertically)."""

    def initStyleOption(self, option, index) -> None:
        super().initStyleOption(option, index)
        alignment = index.data(Qt.TextAlignmentRole)
        if alignment is not None:
            option.displayAlignment = Qt.Alignment(alignment)
        else:
            option.displayAlignment = Qt.AlignLeft | Qt.AlignTop
