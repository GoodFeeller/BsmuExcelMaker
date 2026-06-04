from pathlib import Path

from PySide6.QtCore import QDate
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QFileDialog, QMessageBox, QStatusBar

from app.message_boxes import show_success
from app.modules.duty_formation.model import DutyFormationModel
from app.modules.duty_formation.services.responsible_store import (
    load_settings,
    save_settings,
    specialist_names,
)
from app.modules.duty_formation.services.schedule_aggregator import aggregate_by_groups
from app.modules.duty_formation.services.count_exporter import (
    default_count_output_path,
    export_count_sheet,
)
from app.modules.duty_formation.services.count_row_builder import build_count_rows
from app.modules.duty_formation.services.word_exporter import export_groups_to_word
from app.modules.duty_formation.view import DutyFormationView
from app.modules.duty_formation.widgets.excel_table_view import ExcelTableView
from app.modules.duty_formation.models import SelectedRange
from app.modules.duty_formation.services.workbook_loader_worker import WorkbookLoaderWorker
from app.mvc.base import ControllerBase


class DutyFormationController(ControllerBase):
    def __init__(self, parent_window, status_bar: QStatusBar) -> None:
        super().__init__(parent_window)
        self._status_bar = status_bar
        self._model = DutyFormationModel()
        self._view = DutyFormationView()
        self._loader: WorkbookLoaderWorker | None = None
        self._wire_view()
        self._load_app_settings()

    @property
    def view(self) -> DutyFormationView:
        return self._view

    def _wire_view(self) -> None:
        self._view.back_requested.connect(self._on_back_requested)
        self._view.open_file_requested.connect(self._open_file)
        self._view.export_requested.connect(self._export_to_word)
        self._view.sheet_list.currentRowChanged.connect(self._on_sheet_selected)
        self._view.report_date_edit.dateChanged.connect(self._on_report_date_changed)
        self._view.duty_combo.currentTextChanged.connect(self._on_duty_changed)
        self._view.responsible_settings.mapping_changed.connect(
            self._on_responsible_mapping_changed
        )

        shortcut = QShortcut(QKeySequence.Open, self._view)
        shortcut.activated.connect(self._open_file)

    def _on_back_requested(self) -> None:
        if self._loader is not None and self._loader.isRunning():
            return
        shell = self.parent_window
        if hasattr(shell, "show_home"):
            shell.show_home()

    def update_status(self) -> None:
        self._update_status()

    def on_deactivated(self) -> None:
        if self._loader is not None and self._loader.isRunning():
            self._loader.quit()
            self._loader.wait()
            self._loader = None

    def _load_app_settings(self) -> None:
        entries, report_date, duty_specialist = load_settings()
        if entries:
            self._view.responsible_settings.set_entries(entries)
        self._set_report_date(report_date)
        self._set_duty_specialist(duty_specialist)
        self._refresh_duty_combo()

    def _set_report_date(self, value: str) -> None:
        parsed = QDate.fromString(value, "dd.MM.yyyy")
        if not parsed.isValid():
            parsed = QDate.currentDate()
        self._model.report_date = parsed.toString("dd.MM.yyyy")
        self._view.report_date_edit.blockSignals(True)
        self._view.report_date_edit.setDate(parsed)
        self._view.report_date_edit.blockSignals(False)

    def _on_report_date_changed(self) -> None:
        self._model.report_date = self._view.report_date_edit.date().toString("dd.MM.yyyy")
        self._persist_app_settings()

    def _on_duty_changed(self) -> None:
        self._model.duty_specialist = self._get_duty_specialist()
        self._persist_app_settings()

    def _get_duty_specialist(self) -> str:
        return self._view.duty_combo.currentText().strip()

    def _set_duty_specialist(self, name: str) -> None:
        combo = self._view.duty_combo
        combo.blockSignals(True)
        if name and combo.findText(name) < 0:
            combo.addItem(name)
        if name:
            combo.setCurrentText(name)
        elif combo.count():
            combo.setCurrentIndex(0)
        combo.blockSignals(False)
        self._model.duty_specialist = self._get_duty_specialist()

    def _refresh_duty_combo(self) -> None:
        names = specialist_names(self._view.responsible_settings.get_entries())
        current = self._view.duty_combo.currentText().strip()
        combo = self._view.duty_combo
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(names)
        if current in names:
            combo.setCurrentText(current)
        elif names:
            combo.setCurrentIndex(0)
        combo.blockSignals(False)
        self._model.duty_specialist = self._get_duty_specialist()

    def _persist_app_settings(self) -> None:
        save_settings(
            self._view.responsible_settings.get_entries(),
            self._model.report_date,
            self._get_duty_specialist(),
        )

    def _on_responsible_mapping_changed(self) -> None:
        self._refresh_duty_combo()
        self._persist_app_settings()
        self._refresh_aggregation()

    def _set_loading(self, loading: bool, message: str = "") -> None:
        self._view.set_loading(loading)
        if not loading:
            self._view.set_export_enabled(bool(self._model.aggregated_groups))
        if loading:
            self._status_bar.showMessage(message)
        else:
            self._update_status()

    def _open_file(self) -> None:
        if self._loader is not None and self._loader.isRunning():
            return

        filters = "Excel (*.xlsx *.xlsm *.xls);;Все файлы (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent_window,
            "Открыть Excel файл",
            "",
            filters,
        )
        if not file_path:
            return

        self._start_loading(Path(file_path))

    def _start_loading(self, file_path: Path) -> None:
        if self._loader is not None:
            self._loader.quit()
            self._loader.wait()

        self._model.clear_workbook()
        self._model.current_file = file_path
        self._view.sheet_list.clear()
        while self._view.sheet_stack.count():
            widget = self._view.sheet_stack.widget(0)
            self._view.sheet_stack.removeWidget(widget)
            widget.deleteLater()
        self._view.aggregation_panel.clear()
        self._view.file_label.setText(file_path.name)
        self._view.show_work()
        self._set_loading(True, f"Загрузка {file_path.name}...")

        self._loader = WorkbookLoaderWorker(file_path)
        self._loader.finished.connect(self._on_workbook_loaded)
        self._loader.failed.connect(self._on_workbook_failed)
        self._loader.start()

    def _on_workbook_failed(self, message: str) -> None:
        self._loader = None
        self._model.clear_workbook()
        self._view.file_label.clear()
        self._view.aggregation_panel.clear()
        self._view.set_export_enabled(False)
        self._view.show_welcome()
        self._set_loading(False)
        QMessageBox.critical(
            self.parent_window,
            "Ошибка",
            f"Не удалось открыть файл:\n{message}",
        )

    def _on_workbook_loaded(self, sheets: dict) -> None:
        self._loader = None
        self._model.sheets = sheets
        self._view.sheet_list.clear()
        while self._view.sheet_stack.count():
            widget = self._view.sheet_stack.widget(0)
            self._view.sheet_stack.removeWidget(widget)
            widget.deleteLater()
        self._view.aggregation_panel.clear()

        for sheet_name in sheets:
            view = ExcelTableView(sheet_name)
            view.selection_changed.connect(self._on_selection_changed)
            self._view.sheet_stack.addWidget(view)
            self._view.sheet_list.addItem(sheet_name)

        if self._view.sheet_list.count():
            self._view.sheet_list.setCurrentRow(0)

        name = self._model.current_file.name if self._model.current_file else ""
        self.parent_window.setWindowTitle(f"RCPCST Sheduler — Формирование дежурства — {name}")
        self._view.show_work()
        self._set_loading(False)

    def _ensure_sheet_loaded(self, index: int) -> None:
        if index < 0 or index >= self._view.sheet_stack.count():
            return

        view = self._view.sheet_stack.widget(index)
        if not isinstance(view, ExcelTableView) or view.is_loaded:
            return

        sheet_name = view.sheet_name
        frame = self._model.sheets.get(sheet_name)
        if frame is None:
            return

        self._status_bar.showMessage(f"Отображение листа «{sheet_name}»...")
        view.load_dataframe(frame)
        self._update_status()

    def _on_sheet_selected(self, index: int) -> None:
        if index < 0:
            return

        self._view.sheet_stack.setCurrentIndex(index)
        self._ensure_sheet_loaded(index)
        self._model.selected_range = None
        self._model.aggregated_groups = []
        current_view = self._current_view()
        if current_view and current_view.is_loaded:
            self._model.selected_range = current_view.get_selected_range()
            self._refresh_aggregation()
        else:
            self._view.aggregation_panel.clear()
        self._update_status()

    def _on_selection_changed(self, selected: SelectedRange | None) -> None:
        sender = self.sender()
        current_view = self._current_view()
        if sender is not current_view:
            return
        self._model.selected_range = selected
        self._refresh_aggregation()
        self._update_status()

    def _refresh_aggregation(self) -> None:
        if self._model.selected_range is None:
            self._model.aggregated_groups = []
            self._view.aggregation_panel.clear()
            self._view.set_export_enabled(False)
            return

        mappings = self._view.responsible_settings.get_entries()
        self._model.aggregated_groups = aggregate_by_groups(
            self._model.selected_range,
            responsible_mappings=mappings,
        )
        self._view.aggregation_panel.set_groups(self._model.aggregated_groups)
        self._view.set_export_enabled(bool(self._model.aggregated_groups))

    def _export_to_word(self) -> None:
        if not self._model.aggregated_groups:
            QMessageBox.information(
                self.parent_window,
                "Экспорт",
                "Сначала выделите фрагмент расписания для агрегации.",
            )
            return

        if not self._get_duty_specialist():
            QMessageBox.warning(
                self.parent_window,
                "Экспорт",
                "Выберите дежурного специалиста на панели инструментов.",
            )
            return

        current_view = self._current_view()
        if current_view is None or current_view._frame is None:
            QMessageBox.warning(
                self.parent_window,
                "Экспорт",
                "Откройте лист расписания и выделите фрагмент.",
            )
            return

        if self._model.selected_range is None:
            QMessageBox.information(
                self.parent_window,
                "Экспорт",
                "Выделите фрагмент расписания мышью.",
            )
            return

        default_name = "1. Информация для слушателей.docx"
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent_window,
            "Экспорт отчёта",
            default_name,
            "Документ Word (*.docx)",
        )
        if not file_path:
            return

        if not file_path.lower().endswith(".docx"):
            file_path += ".docx"

        count_path = default_count_output_path(file_path)
        count_rows = build_count_rows(
            current_view._frame,
            self._model.selected_range,
            self._model.report_date,
        )

        try:
            export_groups_to_word(
                self._model.aggregated_groups,
                file_path,
                report_date=self._model.report_date,
                duty_specialist=self._get_duty_specialist(),
            )
            if not count_rows:
                raise ValueError(
                    "В выделении нет строк расписания для листа «Подсчёт»."
                )
            export_count_sheet(count_rows, count_path)
        except Exception as error:
            QMessageBox.critical(
                self.parent_window,
                "Ошибка экспорта",
                f"Не удалось сохранить отчёт:\n{error}",
            )
            return

        show_success(
            self.parent_window,
            "Экспорт",
            f"Сохранено:\n{file_path}\n{count_path}",
        )

    def _current_view(self) -> ExcelTableView | None:
        widget = self._view.sheet_stack.currentWidget()
        if isinstance(widget, ExcelTableView):
            return widget
        return None

    def _current_sheet_name(self) -> str:
        item = self._view.sheet_list.currentItem()
        return item.text() if item else ""

    def _update_status(self) -> None:
        if self._loader is not None and self._loader.isRunning():
            return

        if self._model.current_file is None:
            self._status_bar.showMessage(
                "Формирование дежурства  ·  Ctrl+O — открыть файл"
            )
            return

        sheet_name = self._current_sheet_name()
        parts = [self._model.current_file.name]

        if sheet_name:
            parts.append(f"Лист: {sheet_name}")

        if self._model.selected_range:
            parts.append(f"Диапазон: {self._model.selected_range.address}")
            parts.append(f"Групп: {len(self._model.aggregated_groups)}")
        else:
            parts.append("Выделите фрагмент мышью")

        self._status_bar.showMessage("  ·  ".join(parts))
