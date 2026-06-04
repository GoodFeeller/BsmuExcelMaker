from pathlib import Path

from PySide6.QtCore import QDate
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QFileDialog, QMessageBox, QStatusBar

from app.message_boxes import show_success
from app.modules.duty_formation.services.responsible_store import (
    load_cache,
    load_settings,
    save_settings,
    specialist_names,
)
from app.modules.duty_summary.model import DutySummaryModel
from app.modules.duty_summary.services.count_parser import parse_count_workbook
from app.modules.duty_summary.services.summary_exporter import (
    default_summary_output_path,
    export_summary_to_word,
)
from app.modules.duty_summary.view import DutySummaryView
from app.mvc.base import ControllerBase


class DutySummaryController(ControllerBase):
    def __init__(self, parent_window, status_bar: QStatusBar) -> None:
        super().__init__(parent_window)
        self._status_bar = status_bar
        self._model = DutySummaryModel()
        self._view = DutySummaryView()
        self._wire_view()
        self._load_app_settings()

    @property
    def view(self) -> DutySummaryView:
        return self._view

    def _wire_view(self) -> None:
        self._view.back_requested.connect(self._on_back_requested)
        self._view.open_file_requested.connect(self._open_file)
        self._view.export_requested.connect(self._export_summary)
        self._view.report_date_edit.dateChanged.connect(self._on_report_date_changed)
        self._view.duty_combo.currentTextChanged.connect(self._on_duty_changed)

        shortcut = QShortcut(QKeySequence.Open, self._view)
        shortcut.activated.connect(self._open_file)

    def _on_back_requested(self) -> None:
        shell = self.parent_window
        if hasattr(shell, "show_home"):
            shell.show_home()

    def update_status(self) -> None:
        if self._model.stats is None:
            self._status_bar.showMessage("Откройте файл «2. Подсчет.xlsx»")
            return
        stats = self._model.stats
        self._status_bar.showMessage(
            f"Групп: {stats.groups_count} · посещений: {stats.visits_count} · "
            f"подушно: {stats.cushion_total}"
        )

    def _load_app_settings(self) -> None:
        entries, report_date, duty_specialist = load_settings()
        if not entries:
            entries = load_cache()
        self._set_report_date(report_date)
        self._set_duty_specialist(duty_specialist)
        self._refresh_duty_combo(entries)

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
        self._refresh_preview()

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

    def _refresh_duty_combo(self, entries=None) -> None:
        if entries is None:
            entries, _, _ = load_settings()
        names = specialist_names(entries)
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
        entries, _, _ = load_settings()
        save_settings(
            entries,
            self._model.report_date,
            self._get_duty_specialist(),
        )

    def _refresh_preview(self) -> None:
        self._view.preview.set_stats(self._model.stats, self._model.report_date)

    def _open_file(self) -> None:
        filters = "Excel (*.xlsx *.xlsm);;Все файлы (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent_window,
            "Открыть файл подсчёта",
            "",
            filters,
        )
        if not file_path:
            return

        try:
            stats = parse_count_workbook(file_path)
        except (ValueError, OSError) as error:
            QMessageBox.critical(
                self.parent_window,
                "Ошибка",
                f"Не удалось прочитать файл подсчёта:\n{error}",
            )
            return

        self._model.current_file = file_path
        self._model.stats = stats
        if stats.report_date:
            self._set_report_date(stats.report_date)

        path = Path(file_path)
        self._view.file_label.setText(path.name)
        self.parent_window.setWindowTitle(
            f"RCPCST Sheduler — Сводная информация — {path.name}"
        )
        self._view.show_work()
        self._view.set_export_enabled(True)
        self._refresh_preview()
        self.update_status()

    def _export_summary(self) -> None:
        if self._model.stats is None:
            QMessageBox.warning(
                self.parent_window,
                "Экспорт",
                "Сначала откройте файл «2. Подсчет.xlsx».",
            )
            return

        duty = self._get_duty_specialist()
        if not duty:
            QMessageBox.warning(
                self.parent_window,
                "Экспорт",
                "Укажите дежурного специалиста на панели инструментов.",
            )
            return

        default_path = default_summary_output_path(self._model.current_file or "")
        output_path, _ = QFileDialog.getSaveFileName(
            self.parent_window,
            "Сохранить сводную информацию",
            str(default_path),
            "Word (*.docx)",
        )
        if not output_path:
            return

        try:
            export_summary_to_word(
                self._model.stats,
                report_date=self._model.report_date,
                duty_specialist=duty,
                output_path=output_path,
            )
        except (ValueError, OSError) as error:
            QMessageBox.critical(
                self.parent_window,
                "Ошибка",
                f"Не удалось сохранить документ:\n{error}",
            )
            return

        show_success(
            self.parent_window,
            "Готово",
            f"Сводная информация сохранена:\n{output_path}",
        )
