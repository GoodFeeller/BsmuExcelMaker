from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QStatusBar

from app.modules.duty_formation.controller import DutyFormationController
from app.modules.duty_summary.controller import DutySummaryController
from app.shell.home_view import MODULE_DUTY_FORMATION, MODULE_DUTY_SUMMARY, HomeView


class MainWindow(QMainWindow):
    PAGE_HOME = 0
    PAGE_DUTY_FORMATION = 1
    PAGE_DUTY_SUMMARY = 2

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RCPCST Sheduler")
        self.resize(1400, 760)

        self._stack = QStackedWidget()
        self._home = HomeView()
        self._home.module_selected.connect(self._open_module)

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        self._duty_controller = DutyFormationController(self, self._status_bar)
        self._summary_controller = DutySummaryController(self, self._status_bar)

        self._stack.addWidget(self._home)
        self._stack.addWidget(self._duty_controller.view)
        self._stack.addWidget(self._summary_controller.view)
        self.setCentralWidget(self._stack)

        self._create_menu()
        self.show_home()

    def _create_menu(self) -> None:
        file_menu = self.menuBar().addMenu("Файл")
        exit_action = QAction("Выход", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def show_home(self) -> None:
        self._duty_controller.on_deactivated()
        self._stack.setCurrentIndex(self.PAGE_HOME)
        self.setWindowTitle("RCPCST Sheduler")
        self._status_bar.showMessage("Выберите раздел на главном экране")

    def _open_module(self, module_id: str) -> None:
        if module_id == MODULE_DUTY_FORMATION:
            self._stack.setCurrentIndex(self.PAGE_DUTY_FORMATION)
            self.setWindowTitle("RCPCST Sheduler — Формирование дежурства")
            self._duty_controller.update_status()
        elif module_id == MODULE_DUTY_SUMMARY:
            self._stack.setCurrentIndex(self.PAGE_DUTY_SUMMARY)
            self.setWindowTitle("RCPCST Sheduler — Сводная информация по дежурству")
            self._summary_controller.update_status()

    def closeEvent(self, event) -> None:
        self._duty_controller.on_deactivated()
        super().closeEvent(event)
