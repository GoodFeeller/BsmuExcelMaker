from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QVBoxLayout, QWidget

from app.modules.duty_summary.models import CountSummaryStats

_OVERVIEW_LABELS = (
    "Дата",
    "Количество групп",
    "Посещения кабинетов",
    "Запланировано",
    "Посещения факт",
    "Подушно",
)

_CATEGORY_LABELS = (
    "КО",
    "И",
    "ПК",
    "ПП",
    "Аттестация",
    "Студенты БГМУ",
    "МФИУ",
    "Прочее",
)


def _display(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


class SummaryPreview(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._overview_values: list[QLabel] = []
        self._category_values: list[QLabel] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        overview_box = QGroupBox("Сводные показатели")
        overview_grid = QGridLayout(overview_box)
        overview_grid.setHorizontalSpacing(16)
        overview_grid.setVerticalSpacing(8)
        for row, title in enumerate(_OVERVIEW_LABELS):
            title_label = QLabel(title)
            title_label.setObjectName("summaryPreviewLabel")
            value_label = QLabel("—")
            value_label.setObjectName("summaryPreviewValue")
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value_label.setWordWrap(True)
            overview_grid.addWidget(title_label, row, 0)
            overview_grid.addWidget(value_label, row, 1)
            self._overview_values.append(value_label)

        category_box = QGroupBox("По категориям")
        category_grid = QGridLayout(category_box)
        category_grid.setHorizontalSpacing(16)
        category_grid.setVerticalSpacing(8)
        for row, title in enumerate(_CATEGORY_LABELS):
            title_label = QLabel(title)
            title_label.setObjectName("summaryPreviewLabel")
            value_label = QLabel("—")
            value_label.setObjectName("summaryPreviewValue")
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value_label.setWordWrap(True)
            category_grid.addWidget(title_label, row, 0)
            category_grid.addWidget(value_label, row, 1)
            self._category_values.append(value_label)

        layout.addWidget(overview_box)
        layout.addWidget(category_box)
        layout.addStretch()

    def set_stats(self, stats: CountSummaryStats | None, report_date: str = "") -> None:
        if stats is None:
            for label in self._overview_values + self._category_values:
                label.setText("—")
            return

        overview = [
            report_date or stats.report_date,
            stats.groups_count,
            stats.visits_count,
            stats.plan_total,
            stats.fact_total,
            stats.cushion_total,
        ]
        for label, value in zip(self._overview_values, overview):
            label.setText(_display(value))

        for label, value in zip(self._category_values, stats.category_values):
            label.setText(_display(value))

    def clear(self) -> None:
        self.set_stats(None)
