from pathlib import Path

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTabWidget,
    QToolBar,
)

from app.aggregation_panel import AggregationPanel
from app.excel_table_view import ExcelTableView
from app.models import SelectedRange
from app.schedule_aggregator import aggregate_by_groups
from app.welcome_widget import WelcomeWidget
from app.workbook_loader_worker import WorkbookLoaderWorker


class MainWindow(QMainWindow):
    PAGE_WELCOME = 0
    PAGE_SHEETS = 1

    def __init__(self) -> None:
        super().__init__()
        self._current_file: Path | None = None
        self._selected_range: SelectedRange | None = None
        self._aggregated_groups = []
        self._sheets: dict[str, pd.DataFrame] = {}
        self._loader: WorkbookLoaderWorker | None = None
        self._setup_ui()
        self._update_status()

    def _setup_ui(self) -> None:
        self.setWindowTitle("BsmuExcelWorker")
        self.resize(1400, 760)

        self._stack = QStackedWidget()
        self._welcome = WelcomeWidget()
        self._welcome.open_requested.connect(self._open_file)
        self._stack.addWidget(self._welcome)

        self._work_area = QSplitter(Qt.Horizontal)
        self._work_area.setChildrenCollapsible(False)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._tabs.currentChanged.connect(self._on_tab_changed)
        self._work_area.addWidget(self._tabs)

        self._aggregation_panel = AggregationPanel()
        self._aggregation_panel.setObjectName("aggregationPanel")
        self._work_area.addWidget(self._aggregation_panel)
        self._work_area.setStretchFactor(0, 3)
        self._work_area.setStretchFactor(1, 2)
        self._work_area.setSizes([820, 520])

        self._stack.addWidget(self._work_area)
        self.setCentralWidget(self._stack)

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        self._create_toolbar()
        self._create_menu()

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Основная")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self._open_action = QAction("Открыть файл", self)
        self._open_action.setShortcut(QKeySequence.Open)
        self._open_action.triggered.connect(self._open_file)
        toolbar.addAction(self._open_action)

        self._file_label = QLabel("")
        self._file_label.setObjectName("toolbarFileLabel")
        toolbar.addWidget(self._file_label)

    def _create_menu(self) -> None:
        file_menu = self.menuBar().addMenu("Файл")
        file_menu.addAction(self._open_action)

        file_menu.addSeparator()

        exit_action = QAction("Выход", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def _set_loading(self, loading: bool, message: str = "") -> None:
        self._open_action.setEnabled(not loading)
        if loading:
            self._status_bar.showMessage(message)
        else:
            self._update_status()

    def _open_file(self) -> None:
        if self._loader is not None and self._loader.isRunning():
            return

        filters = "Excel (*.xlsx *.xlsm *.xls);;Все файлы (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть Excel файл", "", filters)
        if not file_path:
            return

        self._start_loading(Path(file_path))

    def _start_loading(self, file_path: Path) -> None:
        if self._loader is not None:
            self._loader.quit()
            self._loader.wait()

        self._current_file = file_path
        self._selected_range = None
        self._aggregated_groups = []
        self._sheets = {}
        self._tabs.clear()
        self._aggregation_panel.clear()
        self._file_label.setText(file_path.name)
        self._stack.setCurrentIndex(self.PAGE_SHEETS)
        self._set_loading(True, f"Загрузка {file_path.name}...")

        self._loader = WorkbookLoaderWorker(file_path)
        self._loader.finished.connect(self._on_workbook_loaded)
        self._loader.failed.connect(self._on_workbook_failed)
        self._loader.start()

    def _on_workbook_failed(self, message: str) -> None:
        self._loader = None
        self._current_file = None
        self._file_label.clear()
        self._aggregation_panel.clear()
        self._stack.setCurrentIndex(self.PAGE_WELCOME)
        self._set_loading(False)
        QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{message}")

    def _on_workbook_loaded(self, sheets: dict) -> None:
        self._loader = None
        self._sheets = sheets
        self._tabs.clear()
        self._aggregation_panel.clear()

        for sheet_name in sheets:
            view = ExcelTableView(sheet_name)
            view.selection_changed.connect(self._on_selection_changed)
            self._tabs.addTab(view, sheet_name)

        if self._tabs.count():
            self._ensure_tab_loaded(0)

        self.setWindowTitle(f"BsmuExcelWorker — {self._current_file.name}")
        self._stack.setCurrentIndex(self.PAGE_SHEETS)
        self._set_loading(False)

    def _ensure_tab_loaded(self, index: int) -> None:
        if index < 0 or index >= self._tabs.count():
            return

        view = self._tabs.widget(index)
        if not isinstance(view, ExcelTableView) or view.is_loaded:
            return

        sheet_name = self._tabs.tabText(index)
        frame = self._sheets.get(sheet_name)
        if frame is None:
            return

        self._status_bar.showMessage(f"Отображение листа «{sheet_name}»...")
        view.load_dataframe(frame)
        self._update_status()

    def _on_tab_changed(self, index: int) -> None:
        if index < 0:
            return

        self._ensure_tab_loaded(index)
        self._selected_range = None
        self._aggregated_groups = []
        current_view = self._current_view()
        if current_view and current_view.is_loaded:
            self._selected_range = current_view.get_selected_range()
            self._refresh_aggregation()
        else:
            self._aggregation_panel.clear()
        self._update_status()

    def _on_selection_changed(self, selected: SelectedRange | None) -> None:
        sender = self.sender()
        current_view = self._current_view()
        if sender is not current_view:
            return
        self._selected_range = selected
        self._refresh_aggregation()
        self._update_status()

    def _refresh_aggregation(self) -> None:
        if self._selected_range is None:
            self._aggregated_groups = []
            self._aggregation_panel.clear()
            return

        self._aggregated_groups = aggregate_by_groups(self._selected_range)
        self._aggregation_panel.set_groups(self._aggregated_groups)

    def _current_view(self) -> ExcelTableView | None:
        widget = self._tabs.currentWidget()
        if isinstance(widget, ExcelTableView):
            return widget
        return None

    def _update_status(self) -> None:
        if self._loader is not None and self._loader.isRunning():
            return

        if self._current_file is None:
            self._status_bar.showMessage("Готово к работе  ·  Ctrl+O — открыть файл")
            return

        sheet_name = self._tabs.tabText(self._tabs.currentIndex()) if self._tabs.count() else ""
        parts = [self._current_file.name]

        if sheet_name:
            parts.append(f"Лист: {sheet_name}")

        if self._selected_range:
            parts.append(f"Диапазон: {self._selected_range.address}")
            parts.append(f"Групп: {len(self._aggregated_groups)}")
        else:
            parts.append("Выделите фрагмент мышью")

        self._status_bar.showMessage("  ·  ".join(parts))

    def closeEvent(self, event) -> None:
        if self._loader is not None and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()
        super().closeEvent(event)
