from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.modules.duty_formation.services.responsible_mapping import (
    ResponsibleEntry,
    parse_rooms_text,
)
from app.modules.duty_formation.services.responsible_store import (
    export_to_json_file,
    import_from_json_file,
)


class ResponsibleSettingsPanel(QWidget):
    mapping_changed = Signal()

    HEADERS = ["Ответственный специалист", "Кабинеты (через запятую)"]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._add_empty_row()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Ответственные специалисты")
        title.setObjectName("aggregationTitle")

        hint = QLabel(
            "Заполните таблицу: имя специалиста и его кабинеты. "
            "В отчёте и в агрегации подставляется только имя из этой таблицы по номеру кабинета. "
            "Данные автоматически сохраняются в кэш; можно импортировать и экспортировать JSON."
        )
        hint.setObjectName("aggregationHint")
        hint.setWordWrap(True)

        self._table = QTableWidget(0, len(self.HEADERS))
        self._table.setHorizontalHeaderLabels(self.HEADERS)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnWidth(0, 300)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.itemChanged.connect(self._on_item_changed)

        row_buttons = QHBoxLayout()
        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self._add_empty_row)
        remove_button = QPushButton("Удалить выбранные")
        remove_button.clicked.connect(self._remove_selected_rows)
        row_buttons.addWidget(add_button)
        row_buttons.addWidget(remove_button)
        row_buttons.addStretch()

        io_buttons = QHBoxLayout()
        import_button = QPushButton("Импорт JSON…")
        import_button.clicked.connect(self._import_json)
        export_button = QPushButton("Экспорт JSON…")
        export_button.clicked.connect(self._export_json)
        io_buttons.addWidget(import_button)
        io_buttons.addWidget(export_button)
        io_buttons.addStretch()

        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(self._table)
        layout.addLayout(row_buttons)
        layout.addLayout(io_buttons)

    def _on_item_changed(self) -> None:
        self.mapping_changed.emit()

    def _add_empty_row(self) -> None:
        row = self._table.rowCount()
        self._table.blockSignals(True)
        self._table.insertRow(row)
        self._table.setItem(row, 0, QTableWidgetItem(""))
        self._table.setItem(row, 1, QTableWidgetItem(""))
        self._table.blockSignals(False)

    def _remove_selected_rows(self) -> None:
        rows = sorted({index.row() for index in self._table.selectedIndexes()}, reverse=True)
        if not rows:
            return
        self._table.blockSignals(True)
        for row in rows:
            self._table.removeRow(row)
        self._table.blockSignals(False)
        if self._table.rowCount() == 0:
            self._add_empty_row()
        self.mapping_changed.emit()

    def set_entries(self, entries: list[ResponsibleEntry]) -> None:
        self._table.blockSignals(True)
        self._table.setRowCount(0)
        if entries:
            for entry in entries:
                row = self._table.rowCount()
                self._table.insertRow(row)
                self._table.setItem(row, 0, QTableWidgetItem(entry.name))
                self._table.setItem(row, 1, QTableWidgetItem(", ".join(entry.rooms)))
        else:
            self._add_empty_row()
        self._table.blockSignals(False)

    def get_entries(self) -> list[ResponsibleEntry]:
        entries: list[ResponsibleEntry] = []
        for row in range(self._table.rowCount()):
            name_item = self._table.item(row, 0)
            rooms_item = self._table.item(row, 1)
            name = name_item.text().strip() if name_item else ""
            rooms_text = rooms_item.text() if rooms_item else ""
            rooms = parse_rooms_text(rooms_text)
            if name and rooms:
                entries.append(ResponsibleEntry(name=name, rooms=rooms))
        return entries

    def _import_json(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Импорт ответственных",
            "",
            "JSON (*.json);;Все файлы (*.*)",
        )
        if not file_path:
            return
        try:
            entries = import_from_json_file(file_path)
        except Exception as error:
            QMessageBox.critical(
                self,
                "Импорт JSON",
                f"Не удалось прочитать файл:\n{error}",
            )
            return
        if not entries:
            QMessageBox.warning(
                self,
                "Импорт JSON",
                "В файле нет записей с именем специалиста и списком кабинетов.",
            )
            return
        self.set_entries(entries)
        self.mapping_changed.emit()

    def _export_json(self) -> None:
        entries = self.get_entries()
        if not entries:
            QMessageBox.information(
                self,
                "Экспорт JSON",
                "Добавьте хотя бы одного специалиста с кабинетами.",
            )
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт ответственных",
            "responsible_specialists.json",
            "JSON (*.json)",
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".json"):
            file_path += ".json"
        try:
            export_to_json_file(entries, file_path)
        except Exception as error:
            QMessageBox.critical(
                self,
                "Экспорт JSON",
                f"Не удалось сохранить файл:\n{error}",
            )
            return
        QMessageBox.information(self, "Экспорт JSON", f"Сохранено:\n{file_path}")
