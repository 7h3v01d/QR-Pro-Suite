"""
QR Professional Suite — Settings Tab
"""

from PyQt6 import QtWidgets, QtCore
from core import AppSettings, show_info
from widgets import SectionHeader, Divider


class SettingsTab(QtWidgets.QWidget):
    settings_changed = QtCore.pyqtSignal()

    def __init__(self, settings: AppSettings):
        super().__init__()
        self.settings = settings
        self._build_ui()

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(20)

        root.addWidget(SectionHeader("Settings", "Application preferences"))
        root.addWidget(Divider())

        # Two-column layout
        cols = QtWidgets.QHBoxLayout()
        cols.setSpacing(20)

        # ── Left column ──────────────────────────────────────────────── #
        left_group = QtWidgets.QGroupBox("Camera & Scanning")
        left_layout = QtWidgets.QFormLayout(left_group)
        left_layout.setSpacing(12)
        left_layout.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        self.camera_spin = QtWidgets.QSpinBox()
        self.camera_spin.setRange(0, 10)
        self.camera_spin.setValue(self.settings.camera_index)
        self.camera_spin.setToolTip("Index of the webcam to use (usually 0)")
        left_layout.addRow("Camera Index:", self.camera_spin)

        self.qr_only_chk = QtWidgets.QCheckBox("QR codes only (improves stability)")
        self.qr_only_chk.setChecked(self.settings.scan_qr_only)
        left_layout.addRow("", self.qr_only_chk)

        cols.addWidget(left_group)

        # ── Right column ─────────────────────────────────────────────── #
        right_group = QtWidgets.QGroupBox("Default Generation Options")
        right_layout = QtWidgets.QFormLayout(right_group)
        right_layout.setSpacing(12)
        right_layout.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        self.size_spin = QtWidgets.QSpinBox()
        self.size_spin.setRange(4, 30)
        self.size_spin.setValue(self.settings.default_size)
        self.size_spin.setSuffix(" px")
        right_layout.addRow("Module Size:", self.size_spin)

        self.border_spin = QtWidgets.QSpinBox()
        self.border_spin.setRange(0, 12)
        self.border_spin.setValue(self.settings.default_border)
        right_layout.addRow("Border (modules):", self.border_spin)

        self.ec_combo = QtWidgets.QComboBox()
        self.ec_combo.addItems(["L (7%)", "M (15%)", "Q (25%)", "H (30%)"])
        ec_map = {"L": 0, "M": 1, "Q": 2, "H": 3}
        self.ec_combo.setCurrentIndex(ec_map.get(self.settings.default_error_correction, 3))
        right_layout.addRow("Error Correction:", self.ec_combo)

        cols.addWidget(right_group)

        root.addLayout(cols)

        # ── Window ───────────────────────────────────────────────────── #
        window_group = QtWidgets.QGroupBox("Window")
        window_layout = QtWidgets.QVBoxLayout(window_group)

        self.ontop_chk = QtWidgets.QCheckBox("Always on top")
        self.ontop_chk.setChecked(self.settings.always_on_top)
        window_layout.addWidget(self.ontop_chk)

        root.addWidget(window_group)

        # ── Save / Reset ─────────────────────────────────────────────── #
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)
        reset_btn = QtWidgets.QPushButton("Reset to Defaults")
        reset_btn.setObjectName("dangerBtn")
        save_btn = QtWidgets.QPushButton("Save Settings")
        save_btn.setObjectName("primaryBtn")
        btn_row.addWidget(reset_btn)
        btn_row.addWidget(save_btn)
        root.addLayout(btn_row)

        root.addStretch(1)

        # About section
        about_frame = QtWidgets.QFrame()
        about_frame.setObjectName("panelFrame")
        about_layout = QtWidgets.QVBoxLayout(about_frame)
        about_layout.setContentsMargins(16, 14, 16, 14)

        about_title = QtWidgets.QLabel("QR Professional Suite")
        about_title.setStyleSheet("color: #E8EAF0; font-size: 15px; font-weight: 700;")
        about_layout.addWidget(about_title)

        about_sub = QtWidgets.QLabel(
            "Built with PyQt6 · qrcode · pyzbar · python-barcode · Pillow\n"
            "Professional QR & Barcode management for power users."
        )
        about_sub.setStyleSheet("color: #4B5563; font-size: 11px; line-height: 1.6;")
        about_layout.addWidget(about_sub)

        root.addWidget(about_frame)

        # Signals
        save_btn.clicked.connect(self._save)
        reset_btn.clicked.connect(self._reset)

    def _save(self):
        self.settings.camera_index = self.camera_spin.value()
        self.settings.scan_qr_only = self.qr_only_chk.isChecked()
        self.settings.default_size = self.size_spin.value()
        self.settings.default_border = self.border_spin.value()
        ec_keys = ["L", "M", "Q", "H"]
        self.settings.default_error_correction = ec_keys[self.ec_combo.currentIndex()]
        self.settings.always_on_top = self.ontop_chk.isChecked()
        self.settings.save()
        self.settings_changed.emit()
        show_info(self, "Settings Saved", "Your preferences have been saved.")

    def _reset(self):
        reply = QtWidgets.QMessageBox.question(
            self, "Reset Settings",
            "Reset all settings to defaults?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.Cancel
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            defaults = AppSettings()
            self.camera_spin.setValue(defaults.camera_index)
            self.qr_only_chk.setChecked(defaults.scan_qr_only)
            self.size_spin.setValue(defaults.default_size)
            self.border_spin.setValue(defaults.default_border)
            self.ec_combo.setCurrentIndex(3)
            self.ontop_chk.setChecked(defaults.always_on_top)
