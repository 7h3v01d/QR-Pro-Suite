"""
QR Professional Suite
─────────────────────────────────────────────────────
Professional QR code and barcode generation & decoding.
Built on PyQt6 · qrcode · pyzbar · python-barcode · Pillow
"""

import sys
import time
import logging
from typing import List

from PyQt6 import QtWidgets, QtGui, QtCore

from core import AppSettings, HistoryModel, HistoryItem
from stylesheet import STYLESHEET
from tab_generate import GeneratorTab
from tab_reader import ReaderTab
from tab_batch import BatchTab
from tab_history import HistoryTab
from tab_settings import SettingsTab


APP_NAME = "QR Professional Suite"
APP_VERSION = "2.0"


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        filename="qr_pro.log",
        filemode="w"
    )
    logging.info(f"{APP_NAME} v{APP_VERSION} starting up.")


class TitleBar(QtWidgets.QWidget):
    """Custom window header strip with app name and version badge."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setStyleSheet("""
            QWidget {
                background: #0A0C10;
                border-bottom: 1px solid #1A1F2E;
            }
        """)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(10)

        # Icon placeholder
        icon_lbl = QtWidgets.QLabel("⬛")
        icon_lbl.setStyleSheet("color: #2563EB; font-size: 16px; background: transparent; border: none;")
        layout.addWidget(icon_lbl)

        name_lbl = QtWidgets.QLabel(APP_NAME)
        name_lbl.setStyleSheet(
            "color: #E8EAF0; font-size: 14px; font-weight: 700; "
            "letter-spacing: 0.02em; background: transparent; border: none;"
        )
        layout.addWidget(name_lbl)

        badge = QtWidgets.QLabel(f"v{APP_VERSION}")
        badge.setStyleSheet("""
            QLabel {
                color: #4B5563;
                background: #141720;
                border: 1px solid #1E2130;
                border-radius: 4px;
                padding: 1px 7px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.08em;
            }
        """)
        layout.addWidget(badge)
        layout.addStretch(1)

        self.session_lbl = QtWidgets.QLabel("")
        self.session_lbl.setStyleSheet("color: #2A3042; font-size: 11px; background: transparent; border: none;")
        layout.addWidget(self.session_lbl)

    def update_session(self, generated: int, decoded: int):
        parts = []
        if generated:
            parts.append(f"{generated} generated")
        if decoded:
            parts.append(f"{decoded} decoded")
        self.session_lbl.setText(" · ".join(parts))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, settings: AppSettings):
        super().__init__()
        self.settings = settings
        self.history_model = HistoryModel()
        self._gen_count = 0
        self._dec_count = 0

        self.setWindowTitle(APP_NAME)
        self.resize(1180, 780)
        self.setMinimumSize(900, 620)

        self._apply_window_flags()
        self._build_ui()
        self._build_menu()
        self._connect_signals()

        logging.info("MainWindow initialised.")

    def _apply_window_flags(self):
        if self.settings.always_on_top:
            self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, True)

    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Title bar
        self.title_bar = TitleBar()
        root.addWidget(self.title_bar)

        # Tabs
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QtWidgets.QTabWidget.TabPosition.North)

        self.gen_tab = GeneratorTab(self.settings)
        self.read_tab = ReaderTab(self.settings)
        self.batch_tab = BatchTab()
        self.hist_tab = HistoryTab(self.history_model)
        self.settings_tab = SettingsTab(self.settings)

        self.tabs.addTab(self.gen_tab, "  Generate  ")
        self.tabs.addTab(self.read_tab, "  Reader  ")
        self.tabs.addTab(self.batch_tab, "  Batch  ")
        self.tabs.addTab(self.hist_tab, "  History  ")
        self.tabs.addTab(self.settings_tab, "  Settings  ")

        root.addWidget(self.tabs)

        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

    def _build_menu(self):
        bar = self.menuBar()

        file_menu = bar.addMenu("&File")
        new_action = QtGui.QAction("New Session", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_session)
        file_menu.addAction(new_action)

        export_history = QtGui.QAction("Export History…", self)
        export_history.triggered.connect(self._export_history)
        file_menu.addAction(export_history)

        file_menu.addSeparator()

        quit_action = QtGui.QAction("Exit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        view_menu = bar.addMenu("&View")
        for i, name in enumerate(["Generate", "Reader", "Batch", "History", "Settings"]):
            act = QtGui.QAction(name, self)
            act.setShortcut(f"Ctrl+{i+1}")
            act.triggered.connect(lambda checked, idx=i: self.tabs.setCurrentIndex(idx))
            view_menu.addAction(act)

        help_menu = bar.addMenu("&Help")
        about_action = QtGui.QAction("About", self)
        about_action.triggered.connect(self._about)
        help_menu.addAction(about_action)

    def _connect_signals(self):
        self.gen_tab.generated.connect(self._on_generated)
        self.read_tab.decoded.connect(self._on_decoded)
        self.batch_tab.generated_many.connect(self._on_many)
        self.batch_tab.decoded_many.connect(self._on_many)
        self.settings_tab.settings_changed.connect(self._apply_settings)
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index: int):
        if self.tabs.widget(index) is not self.read_tab:
            self.read_tab.stop_camera()

    def _on_generated(self, code_type: str, data: str, out_path: str):
        item = HistoryItem(time.time(), "generate", code_type, data, "GUI", out_path)
        self.history_model.add(item)
        self._gen_count += 1
        self.title_bar.update_session(self._gen_count, self._dec_count)
        self.status_bar.showMessage(f"Saved: {out_path}", 4000)

    def _on_decoded(self, code_type: str, data: str, source: str):
        item = HistoryItem(time.time(), "decode", code_type, data, source, "")
        self.history_model.add(item)
        self._dec_count += 1
        self.title_bar.update_session(self._gen_count, self._dec_count)
        self.status_bar.showMessage(f"Decoded: {data[:60]}", 4000)

    def _on_many(self, items: List[HistoryItem]):
        for item in items:
            self.history_model.add(item)
        self.title_bar.update_session(self._gen_count, self._dec_count)

    def _apply_settings(self):
        flag = QtCore.Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlag(flag, self.settings.always_on_top)
        self.show()

    def _new_session(self):
        reply = QtWidgets.QMessageBox.question(
            self, "New Session", "Clear history and start a new session?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.Cancel
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.history_model.clear()
            self._gen_count = 0
            self._dec_count = 0
            self.title_bar.update_session(0, 0)

    def _export_history(self):
        self.tabs.setCurrentWidget(self.hist_tab)
        self.hist_tab._export()

    def _about(self):
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("About QR Professional Suite")
        msg.setText(
            f"<b>QR Professional Suite v{APP_VERSION}</b><br><br>"
            "A comprehensive QR code and barcode tool for power users.<br><br>"
            "<b>Features:</b><br>"
            "• Generate QR codes for 8 different formats<br>"
            "• Gradient and custom color styles<br>"
            "• Embedded logos in QR codes<br>"
            "• Decode from image, drag-and-drop, or live camera<br>"
            "• Batch generate from CSV<br>"
            "• Batch decode entire folders<br>"
            "• Full session history with search and export<br><br>"
            "Built with PyQt6 · qrcode · pyzbar · python-barcode · Pillow"
        )
        msg.exec()

    def closeEvent(self, event):
        self.read_tab.stop_camera()
        self.settings.save()
        event.accept()


def check_dependencies() -> list:
    missing = []
    checks = {
        "Pillow": "PIL",
        "qrcode": "qrcode",
        "pyzbar": "pyzbar",
        "opencv-python": "cv2",
        "python-barcode": "barcode",
    }
    for pkg, mod in checks.items():
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
    return missing


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyleSheet(STYLESHEET)

    missing = check_dependencies()
    if missing:
        QtWidgets.QMessageBox.critical(
            None, "Missing Dependencies",
            f"The following packages are required but not installed:\n\n"
            f"{chr(10).join('  pip install ' + p for p in missing)}\n\n"
            "Please install them and restart the application."
        )
        sys.exit(1)

    settings = AppSettings().load()

    window = MainWindow(settings)
    window.show()

    logging.info("Event loop starting.")
    sys.exit(app.exec())


if __name__ == "__main__":
    setup_logging()
    try:
        main()
    except Exception as e:
        logging.critical("Unhandled top-level exception", exc_info=True)
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        dlg = QtWidgets.QMessageBox()
        dlg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        dlg.setWindowTitle("Fatal Error")
        dlg.setText("The application has crashed.")
        dlg.setInformativeText(
            f"Error: {e}\n\nSee qr_pro.log for full details."
        )
        dlg.exec()
