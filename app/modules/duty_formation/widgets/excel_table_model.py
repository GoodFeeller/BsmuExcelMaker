from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from app.cell_utils import format_cell


class ExcelTableModel(QAbstractTableModel):
    def __init__(self, frame, parent=None) -> None:
        super().__init__(parent)
        self._frame = frame

    @property
    def frame(self):
        return self._frame

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._frame)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._frame.columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignTop
        if role != Qt.DisplayRole:
            return None
        return format_cell(self._frame.iat[index.row(), index.column()])

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.TextAlignmentRole and orientation == Qt.Horizontal:
            return Qt.AlignLeft | Qt.AlignTop
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            from app.modules.duty_formation.models import column_index_to_letter

            return column_index_to_letter(section + 1)
        return str(section + 1)
