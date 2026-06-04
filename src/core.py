"""
QR Professional Suite — Core
Data models, history management, settings, and shared utilities.
"""

import time
import csv
import io
import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import Qt
from PIL import Image


# ─────────────────────────── Data Models ────────────────────────────────── #

@dataclass
class HistoryItem:
    timestamp: float
    action: str
    code_type: str
    data: str
    source: str
    output: str


@dataclass
class AppSettings:
    dark_theme: bool = True
    camera_index: int = 0
    scan_qr_only: bool = False
    default_fg: str = "#000000"
    default_bg: str = "#FFFFFF"
    default_size: int = 10
    default_border: int = 4
    default_error_correction: str = "H"
    recent_paths: List[str] = field(default_factory=list)
    always_on_top: bool = False

    SETTINGS_FILE = "qr_pro_settings.json"

    def save(self):
        try:
            with open(self.SETTINGS_FILE, "w") as f:
                data = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.warning(f"Could not save settings: {e}")

    def load(self):
        try:
            with open(self.SETTINGS_FILE, "r") as f:
                data = json.load(f)
                for k, v in data.items():
                    if hasattr(self, k):
                        setattr(self, k, v)
        except FileNotFoundError:
            pass
        except Exception as e:
            logging.warning(f"Could not load settings: {e}")
        return self


# ─────────────────────────── History Model ──────────────────────────────── #

class HistoryModel(QtCore.QAbstractTableModel):
    HEADERS = ["Time", "Action", "Type", "Data", "Source", "Output"]

    def __init__(self, items: Optional[List[HistoryItem]] = None):
        super().__init__()
        self.items: List[HistoryItem] = items or []

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.items)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.HEADERS)

    def data(self, index: QtCore.QModelIndex, role: int):
        if not index.isValid():
            return None
        item, col = self.items[index.row()], index.column()
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            if col == 0:
                return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item.timestamp))
            elif col == 1:
                return item.action.upper()
            elif col == 2:
                return item.code_type
            elif col == 3:
                return item.data if len(item.data) <= 120 else item.data[:117] + "…"
            elif col == 4:
                return item.source
            elif col == 5:
                return item.output
        if role == Qt.ItemDataRole.ForegroundRole:
            if col == 1:
                if item.action == "generate":
                    return QtGui.QColor("#4FC3F7")
                elif item.action == "decode":
                    return QtGui.QColor("#81C784")
        return None

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return None

    def add(self, item: HistoryItem):
        self.beginInsertRows(QtCore.QModelIndex(), 0, 0)
        self.items.insert(0, item)
        self.endInsertRows()

    def clear(self):
        self.beginResetModel()
        self.items.clear()
        self.endResetModel()

    def export_csv(self, path: str):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)
            for it in self.items:
                writer.writerow([
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(it.timestamp)),
                    it.action, it.code_type, it.data, it.source, it.output
                ])


# ─────────────────────────── Shared Helpers ─────────────────────────────── #

def pil_to_qpixmap(pil_img: Image.Image) -> QtGui.QPixmap:
    if not isinstance(pil_img, Image.Image):
        raise ValueError("Input must be a valid PIL.Image object")
    if pil_img.size == (0, 0):
        raise ValueError("Input image has invalid dimensions")
    target_mode = "RGBA" if pil_img.mode in ["RGBA", "LA", "P"] else "RGB"
    if pil_img.mode != target_mode:
        pil_img = pil_img.convert(target_mode)
    buffer = io.BytesIO()
    try:
        pil_img.save(buffer, format="PNG")
        buffer.seek(0)
        data = buffer.getvalue()
        qimage = QtGui.QImage()
        if not qimage.loadFromData(data, "PNG"):
            raise RuntimeError("Failed to load image data into QImage")
        pixmap = QtGui.QPixmap.fromImage(qimage)
        if pixmap.isNull():
            raise RuntimeError("Failed to create QPixmap from QImage")
        return pixmap
    finally:
        if not buffer.closed:
            buffer.close()


def show_error(parent: QtWidgets.QWidget, title: str, msg: str):
    dlg = QtWidgets.QMessageBox(parent)
    dlg.setIcon(QtWidgets.QMessageBox.Icon.Critical)
    dlg.setWindowTitle(title)
    dlg.setText(msg)
    dlg.exec()


def show_info(parent: QtWidgets.QWidget, title: str, msg: str):
    dlg = QtWidgets.QMessageBox(parent)
    dlg.setIcon(QtWidgets.QMessageBox.Icon.Information)
    dlg.setWindowTitle(title)
    dlg.setText(msg)
    dlg.exec()
