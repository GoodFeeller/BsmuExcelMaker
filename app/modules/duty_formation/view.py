from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QStackedWidget,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.grip_splitter import GripSplitter
from app.modules.duty_formation.widgets.aggregation_panel import AggregationPanel
from app.modules.duty_formation.widgets.responsible_settings_panel import (
    ResponsibleSettingsPanel,
)
from app.modules.duty_formation.widgets.welcome_widget import WelcomeWidget
from app.mvc.base import ViewBase


class DutyFormationView(ViewBase):
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

        self.toolbar = QToolBar("Дежурство")
        self.toolbar.setMovable(False)
        root.addWidget(self.toolbar)

        back_button = QPushButton("← Главная")
        back_button.setObjectName("moduleBackButton")
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.clicked.connect(self.back_requested.emit)
        self.toolbar.addWidget(back_button)
        self.toolbar.addSeparator()

        self.open_action = self.toolbar.addAction("Открыть файл")
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

        self.welcome = WelcomeWidget()
        self.welcome.open_requested.connect(self.open_file_requested.emit)
        self.content_stack.addWidget(self.welcome)

        self.schedule_splitter = GripSplitter(Qt.Horizontal)
        self.schedule_splitter.setObjectName("scheduleSplitter")
        self.schedule_splitter.setChildrenCollapsible(False)
        self.schedule_splitter.setHandleWidth(12)

        excel_area = QWidget()
        excel_layout = QHBoxLayout(excel_area)
        excel_layout.setContentsMargins(0, 0, 0, 0)
        excel_layout.setSpacing(0)

        sheet_sidebar = QWidget()
        sheet_sidebar.setObjectName("sheetSidebar")
        sheet_sidebar_layout = QVBoxLayout(sheet_sidebar)
        sheet_sidebar_layout.setContentsMargins(8, 8, 4, 8)
        sheet_sidebar_layout.setSpacing(6)

        sheet_title = QLabel("Листы")
        sheet_title.setObjectName("sheetSidebarTitle")
        self.sheet_list = QListWidget()
        self.sheet_list.setObjectName("sheetList")
        self.sheet_list.setMinimumWidth(140)
        self.sheet_list.setMaximumWidth(220)

        sheet_sidebar_layout.addWidget(sheet_title)
        sheet_sidebar_layout.addWidget(self.sheet_list)

        self.sheet_stack = QStackedWidget()
        self.sheet_stack.setObjectName("sheetStack")

        excel_layout.addWidget(sheet_sidebar)
        excel_layout.addWidget(self.sheet_stack, stretch=1)

        self.schedule_splitter.addWidget(excel_area)

        self.aggregation_panel = AggregationPanel()
        self.aggregation_panel.setObjectName("aggregationPanel")
        self.schedule_splitter.addWidget(self.aggregation_panel)
        self.schedule_splitter.setStretchFactor(0, 3)
        self.schedule_splitter.setStretchFactor(1, 2)
        self.schedule_splitter.setSizes([820, 520])

        self.work_tabs = QTabWidget()
        self.work_tabs.setDocumentMode(True)
        self.work_tabs.addTab(self.schedule_splitter, "Расписание")

        self.responsible_settings = ResponsibleSettingsPanel()
        self.work_tabs.addTab(self.responsible_settings, "Ответственные")

        self.content_stack.addWidget(self.work_tabs)
        root.addWidget(self.content_stack, stretch=1)

    def show_welcome(self) -> None:
        self.content_stack.setCurrentIndex(self.PAGE_WELCOME)

    def show_work(self) -> None:
        self.content_stack.setCurrentIndex(self.PAGE_WORK)

    def set_export_enabled(self, enabled: bool) -> None:
        self.export_action.setEnabled(enabled)

    def set_loading(self, loading: bool) -> None:
        self.open_action.setEnabled(not loading)
        if loading:
            self.export_action.setEnabled(False)
