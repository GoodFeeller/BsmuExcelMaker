from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QHeaderView, QLabel, QTableView, QVBoxLayout, QWidget

from app.models import GroupAggregate


class AggregationTableModel(QAbstractTableModel):
    HEADERS = [
        "№п/п",
        "Группа",
        "Время занятий",
        "Преподаватель",
        "Ответственный специалист",
        "Симуляционные кабинеты",
    ]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[GroupAggregate] = []

    def set_rows(self, rows: list[GroupAggregate]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.ToolTipRole):
            return None

        row = self._rows[index.row()]
        values = [
            str(row.index),
            row.group,
            row.times_text,
            row.teachers_text,
            row.responsible_text,
            row.rooms_text,
        ]
        return values[index.column()]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return str(section + 1)


class AggregationPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self._title = QLabel("Данные по группам")
        self._title.setObjectName("aggregationTitle")

        self._hint = QLabel("Выделите фрагмент расписания в таблице слева")
        self._hint.setObjectName("aggregationHint")
        self._hint.setWordWrap(True)

        self._table = QTableView()
        self._table.setObjectName("aggregationTable")
        self._model = AggregationTableModel(self)
        self._table.setModel(self._model)
        self._table.setAlternatingRowColors(True)
        self._table.setWordWrap(True)
        self._table.setSelectionBehavior(QTableView.SelectRows)
        self._table.setEditTriggers(QTableView.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table.verticalHeader().setVisible(False)
        self._table.setColumnWidth(0, 48)
        self._table.setColumnWidth(1, 150)
        self._table.setColumnWidth(2, 120)
        self._table.setColumnWidth(3, 150)
        self._table.setColumnWidth(4, 150)

        layout.addWidget(self._title)
        layout.addWidget(self._hint)
        layout.addWidget(self._table)

    def set_groups(self, groups: list[GroupAggregate]) -> None:
        self._model.set_rows(groups)
        if groups:
            self._hint.setText(f"Сформировано записей: {len(groups)}")
            self._table.resizeRowsToContents()
        else:
            self._hint.setText("Выделите фрагмент расписания в таблице слева")
            self._table.resizeRowsToContents()

    def clear(self) -> None:
        self.set_groups([])
