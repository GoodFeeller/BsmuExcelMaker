from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget


class WelcomeWidget(QWidget):
    open_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("welcomeCard")
        card.setFixedWidth(460)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(16)
        card_layout.setAlignment(Qt.AlignCenter)

        title = QLabel("BsmuExcelWorker")
        title.setObjectName("welcomeTitle")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Откройте Excel-файл расписания\nи выделите нужный фрагмент")
        subtitle.setObjectName("welcomeSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)

        open_button = QPushButton("Открыть файл")
        open_button.setObjectName("welcomeOpenButton")
        open_button.setCursor(Qt.PointingHandCursor)
        open_button.clicked.connect(self.open_requested.emit)

        hint = QPushButton("Поддерживаются форматы: .xlsx, .xlsm, .xls")
        hint.setObjectName("welcomeHint")
        hint.setEnabled(False)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(8)
        card_layout.addWidget(open_button, alignment=Qt.AlignCenter)
        card_layout.addWidget(hint)

        layout.addWidget(card)
