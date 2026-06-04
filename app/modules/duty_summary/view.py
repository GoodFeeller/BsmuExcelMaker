from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.modules.duty_summary.widgets.summary_preview import SummaryPreview
from app.modules.duty_summary.widgets.welcome_widget import SummaryWelcomeWidget
from app.mvc.base import ViewBase


class DutySummaryView(ViewBase):
    back_requested = Signal()
    open_file_requested = Signal()
    export_requested = Signal()

    PAGE_WELCOME = 0
    PAGE_WORK = 1

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.toolbar = QToolBar("Сводная информация")
        self.toolbar.setMovable(False)
        root.addWidget(self.toolbar)

        back_button = QPushButton("← Главная")
        back_button.setObjectName("moduleBackButton")
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.clicked.connect(self.back_requested.emit)
        self.toolbar.addWidget(back_button)
        self.toolbar.addSeparator()

        self.open_action = self.toolbar.addAction("Открыть подсчёт")
        self.open_action.triggered.connect(self.open_file_requested.emit)

        self.export_action = self.toolbar.addAction("Экспорт")
        self.export_action.setEnabled(False)
        self.export_action.triggered.connect(self.export_requested.emit)

        self.toolbar.addSeparator()

        date_label = QLabel("Дата отчёта:")
        date_label.setObjectName("toolbarDateLabel")
        self.report_date_edit = QDateEdit()
        self.report_date_edit.setObjectName("reportDateEdit")
        self.report_date_edit.setCalendarPopup(True)
        self.report_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.toolbar.addWidget(date_label)
        self.toolbar.addWidget(self.report_date_edit)

        duty_label = QLabel("Дежурный специалист:")
        duty_label.setObjectName("toolbarDutyLabel")
        self.duty_combo = QComboBox()
        self.duty_combo.setObjectName("dutySpecialistCombo")
        self.duty_combo.setMinimumWidth(240)
        self.toolbar.addWidget(duty_label)
        self.toolbar.addWidget(self.duty_combo)

        self.file_label = QLabel("")
        self.file_label.setObjectName("toolbarFileLabel")
        self.toolbar.addWidget(self.file_label)

        self.content_stack = QStackedWidget()

        self.welcome = SummaryWelcomeWidget()
        self.welcome.open_requested.connect(self.open_file_requested.emit)
        self.content_stack.addWidget(self.welcome)

        work = QWidget()
        work_layout = QHBoxLayout(work)
        work_layout.setContentsMargins(0, 0, 0, 0)
        self.preview = SummaryPreview()
        work_layout.addWidget(self.preview)
        self.content_stack.addWidget(work)

        root.addWidget(self.content_stack, stretch=1)

    def show_welcome(self) -> None:
        self.content_stack.setCurrentIndex(self.PAGE_WELCOME)

    def show_work(self) -> None:
        self.content_stack.setCurrentIndex(self.PAGE_WORK)

    def set_export_enabled(self, enabled: bool) -> None:
        self.export_action.setEnabled(enabled)
