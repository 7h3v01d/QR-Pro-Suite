"""
QR Professional Suite — Custom Widgets
Reusable, polished UI components.
"""

import os
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt


class DropZone(QtWidgets.QLabel):
    """Drag-and-drop image zone with animated feedback."""
    fileDropped = QtCore.pyqtSignal(str)

    def __init__(self, text="Drop an image here\nor click Open Image", parent=None):
        super().__init__(text, parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._default_text = text
        self._update_style(active=False)

    def _update_style(self, active: bool):
        if active:
            self.setStyleSheet("""
                QLabel {
                    border: 2px dashed #3B82F6;
                    border-radius: 10px;
                    background: rgba(37, 99, 235, 0.08);
                    color: #60A5FA;
                    font-size: 13px;
                    font-weight: 600;
                    padding: 20px;
                }
            """)
        else:
            self.setStyleSheet("""
                QLabel {
                    border: 2px dashed #1E2130;
                    border-radius: 10px;
                    background: #0C0E14;
                    color: #4B5563;
                    font-size: 13px;
                    padding: 20px;
                }
            """)

    def dragEnterEvent(self, e: QtGui.QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self._update_style(active=True)

    def dragLeaveEvent(self, e):
        self._update_style(active=False)

    def dropEvent(self, e: QtGui.QDropEvent):
        self._update_style(active=False)
        for url in e.mimeData().urls():
            if os.path.isfile(path := url.toLocalFile()):
                self.fileDropped.emit(path)
                break


class ColorSwatch(QtWidgets.QPushButton):
    """Clickable color swatch with label and dialog integration."""
    colorChanged = QtCore.pyqtSignal(QtGui.QColor)

    def __init__(self, initial_hex: str = "#000000", label: str = "", parent=None):
        super().__init__(parent)
        self._color = QtGui.QColor(initial_hex)
        self._label = label
        self.setFixedSize(80, 34)
        self._refresh()
        self.clicked.connect(self._pick)

    def _pick(self):
        col = QtWidgets.QColorDialog.getColor(
            self._color, self, f"Pick {self._label} Color",
            options=QtWidgets.QColorDialog.ColorDialogOption.ShowAlphaChannel
        )
        if col.isValid():
            self._color = col
            self._refresh()
            self.colorChanged.emit(col)

    def _refresh(self):
        r, g, b = self._color.red(), self._color.green(), self._color.blue()
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        text_col = "#000000" if lum > 140 else "#FFFFFF"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color.name()};
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 6px;
                color: {text_col};
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border: 1px solid rgba(255,255,255,0.35);
            }}
        """)
        self.setText(self._color.name().upper())
        self.setToolTip(f"{self._label}: {self._color.name().upper()}")

    def color(self) -> QtGui.QColor:
        return self._color

    def hex(self) -> str:
        return self._color.name()

    def set_color(self, hex_str: str):
        self._color = QtGui.QColor(hex_str)
        self._refresh()


class PreviewPanel(QtWidgets.QFrame):
    """Image preview panel with copy-to-clipboard action."""

    def __init__(self, placeholder="No image generated yet", parent=None):
        super().__init__(parent)
        self.setObjectName("previewFrame")
        self._pixmap = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QtWidgets.QLabel(placeholder)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("""
            QLabel {
                color: #2A3042;
                font-size: 13px;
                font-weight: 500;
                border: none;
            }
        """)
        self._label.setMinimumSize(200, 200)
        layout.addWidget(self._label)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._ctx_menu)

    def set_pixmap(self, pix: QtGui.QPixmap):
        self._pixmap = pix
        self._scale()

    def _scale(self):
        if self._pixmap:
            size = self.size() - QtCore.QSize(20, 20)
            scaled = self._pixmap.scaled(
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._label.setPixmap(scaled)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._scale()

    def clear(self, text="No image generated yet"):
        self._pixmap = None
        self._label.clear()
        self._label.setText(text)

    def _ctx_menu(self, pos):
        if not self._pixmap:
            return
        menu = QtWidgets.QMenu(self)
        copy_act = menu.addAction("Copy to Clipboard")
        act = menu.exec(self.mapToGlobal(pos))
        if act == copy_act:
            QtWidgets.QApplication.clipboard().setPixmap(self._pixmap)


class StatusChip(QtWidgets.QLabel):
    """Small pill-shaped status indicator."""

    STYLES = {
        "success": ("✓ ", "#22C55E", "rgba(34,197,94,0.12)", "rgba(34,197,94,0.3)"),
        "error":   ("✗ ", "#EF4444", "rgba(239,68,68,0.12)", "rgba(239,68,68,0.3)"),
        "info":    ("● ", "#60A5FA", "rgba(96,165,250,0.12)", "rgba(96,165,250,0.3)"),
        "warn":    ("⚠ ", "#F59E0B", "rgba(245,158,11,0.12)", "rgba(245,158,11,0.3)"),
        "neutral": ("  ", "#6B7280", "rgba(107,114,128,0.12)", "rgba(107,114,128,0.3)"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)

    def set(self, msg: str, kind: str = "info"):
        icon, fg, bg, border = self.STYLES.get(kind, self.STYLES["info"])
        self.setText(f"{icon}{msg}")
        self.setStyleSheet(f"""
            QLabel {{
                color: {fg};
                background: {bg};
                border: 1px solid {border};
                border-radius: 10px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 600;
            }}
        """)
        self.setVisible(True)

    def hide_chip(self):
        self.setVisible(False)


class SectionHeader(QtWidgets.QWidget):
    """Section header with bold label and optional sub-text."""

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(2)

        t = QtWidgets.QLabel(title)
        t.setStyleSheet("color: #E8EAF0; font-size: 18px; font-weight: 700; letter-spacing: -0.01em;")
        layout.addWidget(t)

        if subtitle:
            s = QtWidgets.QLabel(subtitle)
            s.setStyleSheet("color: #4B5563; font-size: 12px;")
            layout.addWidget(s)


class FormRow(QtWidgets.QWidget):
    """Labelled form row."""

    def __init__(self, label: str, widget: QtWidgets.QWidget, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        lbl = QtWidgets.QLabel(label)
        lbl.setFixedWidth(130)
        lbl.setStyleSheet("color: #6B7280; font-size: 12px; font-weight: 500;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(lbl)
        layout.addSpacing(10)
        layout.addWidget(widget, 1)


class Divider(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.setStyleSheet("background: #1E2130; max-height: 1px; border: none;")
