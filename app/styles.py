APP_STYLESHEET = """
QMainWindow {
    background-color: #f1f5f9;
}

QWidget {
    color: #1e293b;
    font-size: 10pt;
}

QMenuBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 2px 0;
}

QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
    border-radius: 6px;
}

QMenuBar::item:selected {
    background-color: #eff6ff;
    color: #1d4ed8;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 28px 8px 16px;
    border-radius: 6px;
}

QMenu::item:selected {
    background-color: #eff6ff;
    color: #1d4ed8;
}

QToolBar {
    background-color: #ffffff;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    spacing: 8px;
    padding: 8px 12px;
}

QToolButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}

QToolButton:hover {
    background-color: #1d4ed8;
}

QToolButton:pressed {
    background-color: #1e40af;
}

QToolButton:disabled {
    background-color: #94a3b8;
    color: #e2e8f0;
}

QLabel#toolbarFileLabel {
    color: #64748b;
    padding-left: 8px;
}

QLabel#toolbarDateLabel,
QLabel#toolbarDutyLabel {
    color: #475569;
    padding-left: 4px;
    font-size: 10pt;
}

QDateEdit#reportDateEdit {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 4px 10px;
    min-width: 118px;
    min-height: 28px;
    font-size: 10pt;
}

QDateEdit#reportDateEdit:focus {
    border-color: #2563eb;
}

QCalendarWidget {
    min-width: 360px;
    min-height: 300px;
    font-size: 12pt;
}

QComboBox#dutySpecialistCombo {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 4px 10px;
    min-height: 28px;
    font-size: 10pt;
}

QTabWidget::pane {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    background-color: #ffffff;
    top: -1px;
    margin: 0 12px 12px 12px;
}

QTabBar {
    qproperty-drawBase: 0;
}

QTabBar::tab {
    background-color: #e2e8f0;
    color: #64748b;
    padding: 10px 18px;
    margin: 12px 4px 0 12px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    min-width: 80px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #2563eb;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    background-color: #cbd5e1;
    color: #334155;
}

QTableView {
    background-color: #ffffff;
    alternate-background-color: #f8fafc;
    border: none;
    gridline-color: #e2e8f0;
    selection-background-color: #93c5fd;
    selection-color: #0f172a;
    outline: none;
}

QTableView::item {
    padding: 4px 10px;
    border: none;
}

QTableView::item:selected {
    background-color: #93c5fd;
}

QHeaderView::section {
    background-color: #f1f5f9;
    color: #475569;
    border: none;
    border-right: 1px solid #e2e8f0;
    border-bottom: 1px solid #e2e8f0;
    padding: 8px 10px;
    font-weight: 600;
}

QHeaderView::section:hover {
    background-color: #e2e8f0;
}

QStatusBar {
    background-color: #ffffff;
    border-top: 1px solid #e2e8f0;
    color: #64748b;
    padding: 4px 12px;
}

QLabel#homeTitle {
    font-size: 24pt;
    font-weight: 700;
    color: #0f172a;
}

QLabel#homeSubtitle {
    font-size: 12pt;
    color: #64748b;
}

QFrame#homeModuleCard {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
}

QLabel#homeModuleNumber {
    font-size: 11pt;
    font-weight: 700;
    color: #2563eb;
}

QLabel#homeModuleTitle {
    font-size: 14pt;
    font-weight: 700;
    color: #0f172a;
}

QLabel#homeModuleDesc {
    font-size: 10pt;
    color: #64748b;
}

QPushButton#homeModuleButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: 600;
}

QPushButton#homeModuleButton:hover {
    background-color: #1d4ed8;
}

QPushButton#moduleBackButton {
    background-color: transparent;
    color: #2563eb;
    border: none;
    font-weight: 600;
    padding: 8px 12px;
}

QPushButton#moduleBackButton:hover {
    color: #1d4ed8;
    text-decoration: underline;
}

QLabel#modulePlaceholderTitle {
    font-size: 18pt;
    font-weight: 700;
    color: #0f172a;
}

QLabel#modulePlaceholderHint {
    font-size: 12pt;
    color: #64748b;
}

QLabel#welcomeTitle {
    font-size: 22pt;
    font-weight: 700;
    color: #0f172a;
}

QLabel#welcomeSubtitle {
    font-size: 11pt;
    color: #64748b;
}

QFrame#welcomeCard {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
}

QPushButton#welcomeOpenButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 12px 24px;
    font-size: 11pt;
    font-weight: 600;
    min-width: 200px;
}

QPushButton#welcomeOpenButton:hover {
    background-color: #1d4ed8;
}

QPushButton#welcomeOpenButton:pressed {
    background-color: #1e40af;
}

QPushButton#welcomeHint {
    background-color: transparent;
    color: #64748b;
    border: 1px dashed #cbd5e1;
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 9pt;
}

QLabel#aggregationTitle {
    font-size: 13pt;
    font-weight: 700;
    color: #0f172a;
}

QLabel#aggregationHint {
    color: #64748b;
    font-size: 9pt;
}

QWidget#aggregationPanel {
    background-color: #ffffff;
    border-left: 1px solid #e2e8f0;
}

QTableView#aggregationTable {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    background-color: #ffffff;
}

QWidget#sheetSidebar {
    background-color: #f8fafc;
    border-right: 1px solid #e2e8f0;
}

QLabel#sheetSidebarTitle {
    color: #475569;
    font-size: 9pt;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QListWidget#sheetList {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}

QListWidget#sheetList::item {
    padding: 8px 10px;
    border-radius: 6px;
    margin: 2px 0;
}

QListWidget#sheetList::item:selected {
    background-color: #dbeafe;
    color: #1d4ed8;
    font-weight: 600;
}

QListWidget#sheetList::item:hover:!selected {
    background-color: #f1f5f9;
}

QSplitter#scheduleSplitter::handle:horizontal {
    background-color: transparent;
    width: 14px;
    margin: 8px 0;
}
"""
