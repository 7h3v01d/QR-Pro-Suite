"""
QR Professional Suite — Stylesheet
Dark, refined UI theme.
"""

STYLESHEET = """
/* ── Global ─────────────────────────────────────────────────────────── */
* {
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    color: #E8EAF0;
}

QMainWindow, QDialog {
    background-color: #0F1117;
}

QWidget {
    background-color: #0F1117;
    color: #E8EAF0;
}

/* ── Tab Bar ─────────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #1E2130;
    border-radius: 0px;
    background: #0F1117;
    top: -1px;
}

QTabBar {
    background: #0A0C10;
}

QTabBar::tab {
    background: transparent;
    color: #6B7280;
    padding: 12px 28px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border: none;
    border-bottom: 2px solid transparent;
    min-width: 100px;
}

QTabBar::tab:hover {
    color: #C0C8D8;
    background: rgba(255, 255, 255, 0.03);
}

QTabBar::tab:selected {
    color: #60A5FA;
    border-bottom: 2px solid #60A5FA;
    background: rgba(96, 165, 250, 0.06);
}

/* ── Buttons ─────────────────────────────────────────────────────────── */
QPushButton {
    background-color: #1A1F2E;
    color: #C0C8D8;
    border: 1px solid #2A3042;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.03em;
}

QPushButton:hover {
    background-color: #222840;
    border-color: #3A4560;
    color: #E8EAF0;
}

QPushButton:pressed {
    background-color: #151A28;
    border-color: #60A5FA;
}

QPushButton#primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #2563EB, stop:1 #1D4ED8);
    border: none;
    color: #FFFFFF;
    font-weight: 700;
    letter-spacing: 0.05em;
    padding: 10px 28px;
    border-radius: 6px;
}

QPushButton#primaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #3B82F6, stop:1 #2563EB);
}

QPushButton#primaryBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1D4ED8, stop:1 #1E3A8A);
}

QPushButton#dangerBtn {
    background-color: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #F87171;
}

QPushButton#dangerBtn:hover {
    background-color: rgba(239, 68, 68, 0.2);
    border-color: #EF4444;
}

/* ── Line Edits & Text Areas ─────────────────────────────────────────── */
QLineEdit, QPlainTextEdit, QTextEdit {
    background-color: #141720;
    border: 1px solid #1E2130;
    border-radius: 6px;
    padding: 8px 12px;
    color: #E8EAF0;
    selection-background-color: #2563EB;
}

QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {
    border-color: #3B82F6;
    background-color: #161B28;
}

QLineEdit:disabled {
    background-color: #0E1018;
    color: #4B5563;
    border-color: #161A24;
}

/* ── ComboBox ────────────────────────────────────────────────────────── */
QComboBox {
    background-color: #141720;
    border: 1px solid #1E2130;
    border-radius: 6px;
    padding: 7px 12px;
    color: #E8EAF0;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #3B82F6;
}

QComboBox:focus {
    border-color: #3B82F6;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    width: 10px;
    height: 10px;
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #6B7280;
}

QComboBox QAbstractItemView {
    background-color: #141720;
    border: 1px solid #2A3042;
    selection-background-color: #1D4ED8;
    color: #E8EAF0;
    padding: 4px;
}

/* ── Spin Box ────────────────────────────────────────────────────────── */
QSpinBox {
    background-color: #141720;
    border: 1px solid #1E2130;
    border-radius: 6px;
    padding: 7px 10px;
    color: #E8EAF0;
}

QSpinBox:focus {
    border-color: #3B82F6;
}

QSpinBox::up-button, QSpinBox::down-button {
    background: #1A1F2E;
    border: none;
    width: 18px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background: #222840;
}

/* ── CheckBox ────────────────────────────────────────────────────────── */
QCheckBox {
    spacing: 8px;
    color: #C0C8D8;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #2A3042;
    background: #141720;
}

QCheckBox::indicator:checked {
    background: #2563EB;
    border-color: #2563EB;
}

QCheckBox::indicator:hover {
    border-color: #3B82F6;
}

/* ── Group Box ───────────────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #1E2130;
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px 12px 8px 12px;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #4B5563;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    top: -1px;
    padding: 0 6px;
    background-color: #0F1117;
    color: #6B7280;
    letter-spacing: 0.1em;
}

/* ── Table View ──────────────────────────────────────────────────────── */
QTableView {
    background-color: #0C0E14;
    alternate-background-color: #0F1117;
    gridline-color: #161A24;
    border: 1px solid #1E2130;
    border-radius: 6px;
    selection-background-color: rgba(37, 99, 235, 0.25);
    selection-color: #E8EAF0;
}

QTableView::item {
    padding: 8px 12px;
    border: none;
}

QTableView::item:hover {
    background: rgba(255, 255, 255, 0.04);
}

QHeaderView::section {
    background-color: #0A0C10;
    border: none;
    border-right: 1px solid #1E2130;
    border-bottom: 1px solid #1E2130;
    padding: 8px 12px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #4B5563;
}

QHeaderView::section:hover {
    color: #9CA3AF;
}

/* ── Scrollbars ──────────────────────────────────────────────────────── */
QScrollBar:vertical {
    background: #0A0C10;
    width: 8px;
    border: none;
}

QScrollBar::handle:vertical {
    background: #1E2130;
    border-radius: 4px;
    min-height: 32px;
}

QScrollBar::handle:vertical:hover {
    background: #2A3042;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #0A0C10;
    height: 8px;
    border: none;
}

QScrollBar::handle:horizontal {
    background: #1E2130;
    border-radius: 4px;
    min-width: 32px;
}

QScrollBar::handle:horizontal:hover {
    background: #2A3042;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ── Menu Bar ────────────────────────────────────────────────────────── */
QMenuBar {
    background-color: #0A0C10;
    border-bottom: 1px solid #1E2130;
    padding: 2px;
    color: #9CA3AF;
    font-size: 12px;
}

QMenuBar::item:selected {
    background: rgba(255, 255, 255, 0.06);
    color: #E8EAF0;
    border-radius: 4px;
}

QMenu {
    background-color: #141720;
    border: 1px solid #2A3042;
    border-radius: 6px;
    padding: 4px;
    color: #E8EAF0;
}

QMenu::item {
    padding: 7px 22px 7px 14px;
    border-radius: 4px;
}

QMenu::item:selected {
    background: rgba(37, 99, 235, 0.3);
}

QMenu::separator {
    height: 1px;
    background: #1E2130;
    margin: 4px 8px;
}

/* ── Labels ──────────────────────────────────────────────────────────── */
QLabel {
    background: transparent;
    color: #9CA3AF;
}

QLabel#titleLabel {
    color: #E8EAF0;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.02em;
}

QLabel#sectionLabel {
    color: #4B5563;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

QLabel#valueLabel {
    color: #E8EAF0;
    font-size: 13px;
    font-weight: 500;
}

/* ── Frames / Preview Areas ──────────────────────────────────────────── */
QFrame#previewFrame {
    background-color: #0A0C10;
    border: 1px solid #1E2130;
    border-radius: 10px;
}

QFrame#panelFrame {
    background-color: #0C0E14;
    border: 1px solid #1A1F2E;
    border-radius: 8px;
}

/* ── Sliders ─────────────────────────────────────────────────────────── */
QSlider::groove:horizontal {
    height: 4px;
    background: #1E2130;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #3B82F6;
    width: 14px;
    height: 14px;
    border-radius: 7px;
    margin: -5px 0;
}

QSlider::handle:horizontal:hover {
    background: #60A5FA;
}

QSlider::sub-page:horizontal {
    background: #2563EB;
    border-radius: 2px;
}

/* ── ToolTips ────────────────────────────────────────────────────────── */
QToolTip {
    background-color: #1A1F2E;
    border: 1px solid #2A3042;
    color: #E8EAF0;
    padding: 5px 10px;
    border-radius: 4px;
    font-size: 12px;
}

/* ── Status Bar ──────────────────────────────────────────────────────── */
QStatusBar {
    background: #0A0C10;
    border-top: 1px solid #1E2130;
    color: #4B5563;
    font-size: 11px;
    padding: 0 8px;
}

/* ── Progress Bar ────────────────────────────────────────────────────── */
QProgressBar {
    background: #141720;
    border: 1px solid #1E2130;
    border-radius: 4px;
    height: 6px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2563EB, stop:1 #7C3AED);
    border-radius: 4px;
}

/* ── Radio Button ────────────────────────────────────────────────────── */
QRadioButton {
    spacing: 8px;
    color: #C0C8D8;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 1px solid #2A3042;
    background: #141720;
}

QRadioButton::indicator:checked {
    background: #2563EB;
    border-color: #2563EB;
}

/* ── Splitter ────────────────────────────────────────────────────────── */
QSplitter::handle {
    background: #1E2130;
    width: 1px;
    height: 1px;
}

QSplitter::handle:hover {
    background: #3B82F6;
}
"""
