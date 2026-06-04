from dataclasses import dataclass

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QHeaderView, QLabel, QTableView, QVBoxLayout, QWidget

from app.modules.duty_formation.models import GroupAggregate
from app.modules.duty_formation.services.responsible_mapping import (
    responsible_merge_spans_for_group,
)
from app.modules.duty_formation.services.schedule_aggregator import (
    _schedule_blocks,
    _schedule_line_has_content,
)
from app.modules.duty_formation.widgets.aggregation_delegate import (
    GROUP_BORDER_AFTER_ROLE,
    TIME_BORDER_AFTER_ROLE,
    AggregationItemDelegate,
)


@dataclass
class _FlatRow:
    group: GroupAggregate
    line_index: int
    show_group_meta: bool


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
        self._rows: list[_FlatRow] = []
        self._group_border_rows: set[int] = set()

    def set_groups(self, groups: list[GroupAggregate]) -> None:
        self.beginResetModel()
        flat: list[_FlatRow] = []
        group_border_rows: set[int] = set()
        last_group_with_rows = next(
            (
                index
                for index in range(len(groups) - 1, -1, -1)
                if any(
                    _schedule_line_has_content(
                        line.time,
                        line.teacher,
                        line.responsible,
                        line.room,
                    )
                    for line in groups[index].lines
                )
            ),
            None,
        )

        for group_index, group in enumerate(groups):
            visible_lines = [
                (line_index, line)
                for line_index, line in enumerate(group.lines)
                if _schedule_line_has_content(
                    line.time,
                    line.teacher,
                    line.responsible,
                    line.room,
                )
            ]
            if not visible_lines:
                continue
            for visible_index, (line_index, _line) in enumerate(visible_lines):
                flat.append(
                    _FlatRow(
                        group=group,
                        line_index=line_index,
                        show_group_meta=visible_index == 0,
                    )
                )
            if (
                last_group_with_rows is not None
                and group_index != last_group_with_rows
            ):
                group_border_rows.add(len(flat) - 1)

        self._rows = flat
        self._group_border_rows = group_border_rows
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
        if not index.isValid():
            return None

        flat = self._rows[index.row()]
        line = (
            flat.group.lines[flat.line_index]
            if flat.group.lines
            else None
        )

        row_index = index.row()
        if role == GROUP_BORDER_AFTER_ROLE:
            return row_index in self._group_border_rows

        if role == TIME_BORDER_AFTER_ROLE:
            if row_index in self._group_border_rows:
                return False
            return bool(line and line.border_after)

        if role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignTop

        if role not in (Qt.DisplayRole, Qt.ToolTipRole):
            return None

        if line is None:
            values = [
                str(flat.group.index) if flat.show_group_meta else "",
                flat.group.group if flat.show_group_meta else "",
                "",
                "",
                "",
                "",
            ]
        else:
            values = [
                str(flat.group.index) if flat.show_group_meta else "",
                flat.group.group if flat.show_group_meta else "",
                line.time,
                line.teacher,
                line.responsible,
                line.room,
            ]
        return values[index.column()]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.TextAlignmentRole and orientation == Qt.Horizontal:
            return Qt.AlignLeft | Qt.AlignTop
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
        self._table.setItemDelegate(AggregationItemDelegate(self._table))
        self._table.setAlternatingRowColors(False)
        self._table.setWordWrap(False)
        self._table.setShowGrid(True)
        self._table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._table.setSelectionBehavior(QTableView.SelectRows)
        self._table.setEditTriggers(QTableView.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table.verticalHeader().setVisible(False)
        self._table.setColumnWidth(0, 48)
        self._table.setColumnWidth(1, 150)
        self._table.setColumnWidth(2, 120)
        self._table.setColumnWidth(3, 150)
        self._table.setColumnWidth(4, 190)

        layout.addWidget(self._title)
        layout.addWidget(self._hint)
        layout.addWidget(self._table)

    def _reset_table_spans(self) -> None:
        rows = self._model.rowCount()
        cols = self._model.columnCount()
        for row in range(rows):
            for col in range(cols):
                self._table.setSpan(row, col, 1, 1)

    def _apply_cell_spans(self, groups: list[GroupAggregate]) -> None:
        """Внутри блока времени объединяем «Время» и «Преподаватель»; группу — по всей высоте."""
        self._reset_table_spans()
        table_row = 0

        for group in groups:
            visible = [
                line
                for line in group.lines
                if _schedule_line_has_content(
                    line.time,
                    line.teacher,
                    line.responsible,
                    line.room,
                )
            ]
            if not visible:
                continue

            row_count = len(visible)
            if row_count > 1:
                self._table.setSpan(table_row, 0, row_count, 1)
                self._table.setSpan(table_row, 1, row_count, 1)

            times = [line.time for line in visible]
            responsibles = [line.responsible for line in visible]
            for block_start, block_end in _schedule_blocks(times):
                span = block_end - block_start
                if span > 1:
                    self._table.setSpan(table_row + block_start, 2, span, 1)
                    self._table.setSpan(table_row + block_start, 3, span, 1)

            for rel_start, rel_end in responsible_merge_spans_for_group(responsibles):
                merge_span = rel_end - rel_start
                if merge_span > 1:
                    self._table.setSpan(table_row + rel_start, 4, merge_span, 1)

            table_row += row_count

    def set_groups(self, groups: list[GroupAggregate]) -> None:
        self._model.set_groups(groups)
        self._apply_cell_spans(groups)
        if groups:
            line_count = sum(
                len(
                    [
                        line
                        for line in group.lines
                        if _schedule_line_has_content(
                            line.time,
                            line.teacher,
                            line.responsible,
                            line.room,
                        )
                    ]
                )
                for group in groups
            )
            self._hint.setText(
                f"Сформировано групп: {len(groups)}  ·  строк: {line_count}"
            )
            self._table.resizeRowsToContents()
        else:
            self._hint.setText("Выделите фрагмент расписания в таблице слева")
            self._table.resizeRowsToContents()

    def clear(self) -> None:
        self.set_groups([])
