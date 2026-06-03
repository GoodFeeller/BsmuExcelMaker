from pathlib import Path

from PySide6.QtCore import QThread, Signal

from app.excel_loader import load_workbook


class WorkbookLoaderWorker(QThread):
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, file_path: str | Path) -> None:
        super().__init__()
        self._file_path = Path(file_path)

    def run(self) -> None:
        try:
            sheets = load_workbook(self._file_path)
            self.finished.emit(sheets)
        except Exception as exc:
            self.failed.emit(str(exc))
