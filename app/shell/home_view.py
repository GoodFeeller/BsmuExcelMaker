from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.mvc.base import ViewBase

MODULE_DUTY_FORMATION = "duty_formation"
MODULE_DUTY_SUMMARY = "duty_summary"


class HomeView(ViewBase):
    module_selected = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        header = QLabel("RCPCST Sheduler")
        header.setObjectName("homeTitle")
        header.setAlignment(Qt.AlignCenter)
        subtitle = QLabel("Выберите раздел")
        subtitle.setObjectName("homeSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(24)

        grid.addWidget(
            self._module_card(
                "Формирование дежурства",
                "Excel-расписание, агрегация по группам, экспорт в Word",
                MODULE_DUTY_FORMATION,
            ),
            0,
            0,
        )
        grid.addWidget(
            self._module_card(
                "Формирование сводной информации по дежурству",
                "Импорт «2. Подсчет.xlsx», формирование «3. Сводная информация.docx»",
                MODULE_DUTY_SUMMARY,
            ),
            0,
            1,
        )

        layout.addWidget(header)
        layout.addWidget(subtitle)
        layout.addSpacing(24)
        layout.addWidget(grid_host)

    def _module_card(
        self,
        title: str,
        description: str,
        module_id: str,
    ) -> QFrame:
        card = QFrame()
        card.setObjectName("homeModuleCard")
        card.setFixedWidth(360)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setObjectName("homeModuleTitle")
        title_label.setWordWrap(True)

        desc_label = QLabel(description)
        desc_label.setObjectName("homeModuleDesc")
        desc_label.setWordWrap(True)

        open_button = QPushButton("Открыть")
        open_button.setObjectName("homeModuleButton")
        open_button.setCursor(Qt.PointingHandCursor)
        open_button.clicked.connect(lambda: self.module_selected.emit(module_id))

        card_layout.addWidget(title_label)
        card_layout.addWidget(desc_label)
        card_layout.addSpacing(8)
        card_layout.addWidget(open_button, alignment=Qt.AlignLeft)

        return card
