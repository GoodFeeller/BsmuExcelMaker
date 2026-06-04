from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class SummaryWelcomeWidget(QWidget):
    open_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Формирование сводной информации по дежурству")
        title.setObjectName("welcomeTitle")
        title.setAlignment(Qt.AlignCenter)

        hint = QLabel(
            "Откройте файл «2. Подсчет.xlsx», проверьте сводные показатели "
            "и экспортируйте «3. Сводная информация.docx»."
        )
        hint.setObjectName("welcomeHint")
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        hint.setMaximumWidth(520)

        button = QPushButton("Открыть файл подсчёта")
        button.setObjectName("welcomeOpenButton")
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(self.open_requested.emit)

        layout.addWidget(title)
        layout.addSpacing(8)
        layout.addWidget(hint)
        layout.addSpacing(16)
        layout.addWidget(button, alignment=Qt.AlignCenter)
