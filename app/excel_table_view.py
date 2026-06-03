import pandas as pd
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableView

from app.cell_utils import format_cell
from app.excel_table_model import ExcelTableModel
from app.models import SelectedRange


class ExcelTableView(QTableView):
    selection_changed = Signal(object)

    def __init__(self, sheet_name: str = "", parent=None) -> None:
        super().__init__(parent)
        self._sheet_name = sheet_name
        self._frame: pd.DataFrame | None = None
        self._model: ExcelTableModel | None = None
        self._loaded = False

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setWordWrap(False)
        self.setShowGrid(True)
        self.setCornerButtonEnabled(True)
        self.horizontalHeader().setHighlightSections(False)
        self.verticalHeader().setHighlightSections(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.horizontalHeader().setDefaultSectionSize(96)
        self.verticalHeader().setDefaultSectionSize(24)

    @property
    def sheet_name(self) -> str:
        return self._sheet_name

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def set_sheet_name(self, sheet_name: str) -> None:
        self._sheet_name = sheet_name

    def load_dataframe(self, frame: pd.DataFrame) -> None:
        self._frame = frame
        self._model = ExcelTableModel(frame, self)
        self.setModel(self._model)
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._loaded = True
        self.clearSelection()
        self.selection_changed.emit(None)

    def get_selected_range(self) -> SelectedRange | None:
        if self._frame is None:
            return None

        indexes = self.selectedIndexes()
        if not indexes:
            return None

        rows = sorted(index.row() for index in indexes)
        cols = sorted(index.column() for index in indexes)
        top_row = rows[0] + 1
        bottom_row = rows[-1] + 1
        left_col = cols[0] + 1
        right_col = cols[-1] + 1

        data: list[list] = []
        for row in range(rows[0], rows[-1] + 1):
            row_data: list[str] = []
            for col in range(cols[0], cols[-1] + 1):
                row_data.append(format_cell(self._frame.iat[row, col]))
            data.append(row_data)

        return SelectedRange(
            sheet_name=self._sheet_name,
            top_row=top_row,
            left_col=left_col,
            bottom_row=bottom_row,
            right_col=right_col,
            data=data,
        )

    def _on_selection_changed(self) -> None:
        self.selection_changed.emit(self.get_selected_range())
