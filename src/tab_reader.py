"""
QR Professional Suite — Reader Tab
Decode QR codes and barcodes from images, files, or live camera.
"""

import logging
from typing import Optional

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt
from PIL import Image
import cv2

from pyzbar.pyzbar import decode as zbar_decode, ZBarSymbol

from core import AppSettings, pil_to_qpixmap, show_error
from widgets import DropZone, PreviewPanel, StatusChip, SectionHeader, Divider


class ResultCard(QtWidgets.QFrame):
    """Individual decode result card."""

    copyRequested = QtCore.pyqtSignal(str)
    urlRequested = QtCore.pyqtSignal(str)

    def __init__(self, index: int, code_type: str, data: str, parent=None):
        super().__init__(parent)
        self.data = data
        self.setObjectName("panelFrame")
        self.setStyleSheet("""
            QFrame#panelFrame {
                background: #0C0E14;
                border: 1px solid #1A1F2E;
                border-radius: 8px;
            }
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Header row
        hdr = QtWidgets.QHBoxLayout()
        idx_lbl = QtWidgets.QLabel(f"#{index}")
        idx_lbl.setStyleSheet("color: #2A3042; font-size: 11px; font-weight: 700;")
        type_chip = QtWidgets.QLabel(code_type)
        type_chip.setStyleSheet("""
            QLabel {
                color: #60A5FA;
                background: rgba(96, 165, 250, 0.1);
                border: 1px solid rgba(96, 165, 250, 0.25);
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.08em;
            }
        """)
        hdr.addWidget(idx_lbl)
        hdr.addWidget(type_chip)
        hdr.addStretch(1)

        copy_btn = QtWidgets.QPushButton("Copy")
        copy_btn.setFixedSize(60, 24)
        copy_btn.setStyleSheet("""
            QPushButton {
                background: #1A1F2E;
                border: 1px solid #2A3042;
                border-radius: 4px;
                color: #9CA3AF;
                font-size: 11px;
            }
            QPushButton:hover { color: #E8EAF0; border-color: #3A4560; }
        """)
        copy_btn.clicked.connect(lambda: self.copyRequested.emit(data))
        hdr.addWidget(copy_btn)

        layout.addLayout(hdr)

        # Data text
        data_lbl = QtWidgets.QLabel(data[:500] + ("…" if len(data) > 500 else ""))
        data_lbl.setWordWrap(True)
        data_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        data_lbl.setStyleSheet("color: #E8EAF0; font-size: 12px; font-family: 'Consolas', monospace;")
        layout.addWidget(data_lbl)

        # URL button
        is_url = any(p in data.lower() for p in ("http://", "https://"))
        if is_url:
            url_btn = QtWidgets.QPushButton("Open URL in Browser →")
            url_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #60A5FA;
                    font-size: 11px;
                    text-align: left;
                    padding: 2px 0;
                }
                QPushButton:hover { color: #93C5FD; }
            """)
            url_btn.clicked.connect(lambda: self.urlRequested.emit(data))
            layout.addWidget(url_btn)


class ReaderTab(QtWidgets.QWidget):
    decoded = QtCore.pyqtSignal(str, str, str)

    def __init__(self, settings: AppSettings):
        super().__init__()
        self.settings = settings
        self.cap = None
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(60)
        self.timer.timeout.connect(self._read_frame)
        self._last_decoded: Optional[str] = None

        self._build_ui()
        self._connect_signals()

    # ── UI ───────────────────────────────────────────────────────────── #

    def _build_ui(self):
        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(20)

        # Left — controls + results
        left = QtWidgets.QWidget()
        left.setObjectName("panelFrame")
        left.setFixedWidth(360)
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(12)

        left_layout.addWidget(SectionHeader("Reader", "Decode codes from images or camera"))
        left_layout.addWidget(Divider())

        # Source controls
        src_label = QtWidgets.QLabel("INPUT SOURCE")
        src_label.setObjectName("sectionLabel")
        left_layout.addWidget(src_label)

        btn_row = QtWidgets.QHBoxLayout()
        self.open_btn = QtWidgets.QPushButton("Open Image…")
        self.cam_btn = QtWidgets.QPushButton("Start Camera")
        self.cam_btn.setObjectName("primaryBtn")
        btn_row.addWidget(self.open_btn)
        btn_row.addWidget(self.cam_btn)
        left_layout.addLayout(btn_row)

        self.qr_only_chk = QtWidgets.QCheckBox("QR codes only (more stable)")
        self.qr_only_chk.setChecked(self.settings.scan_qr_only)
        left_layout.addWidget(self.qr_only_chk)

        left_layout.addWidget(Divider())

        # Results
        results_label = QtWidgets.QLabel("DECODED RESULTS")
        results_label.setObjectName("sectionLabel")
        left_layout.addWidget(results_label)

        self.status_chip = StatusChip()
        left_layout.addWidget(self.status_chip)

        self.results_scroll = QtWidgets.QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.results_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.results_container = QtWidgets.QWidget()
        self.results_layout = QtWidgets.QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(8)
        self.results_layout.addStretch(1)
        self.results_scroll.setWidget(self.results_container)
        left_layout.addWidget(self.results_scroll, 1)

        copy_all_btn = QtWidgets.QPushButton("Copy All Results")
        left_layout.addWidget(copy_all_btn)
        self.copy_all_btn = copy_all_btn

        root.addWidget(left)

        # Right — image / camera feed
        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        drop_hdr = QtWidgets.QLabel("IMAGE / CAMERA FEED")
        drop_hdr.setObjectName("sectionLabel")
        right_layout.addWidget(drop_hdr)

        self.drop_zone = DropZone("Drop an image here\nor use Open Image / Start Camera")
        self.drop_zone.setMinimumHeight(60)
        right_layout.addWidget(self.drop_zone)

        self.preview = PreviewPanel("Camera feed and image previews appear here")
        right_layout.addWidget(self.preview, 1)

        root.addWidget(right, 1)

    def _connect_signals(self):
        self.open_btn.clicked.connect(self._open_image)
        self.cam_btn.clicked.connect(self._toggle_camera)
        self.drop_zone.fileDropped.connect(self._decode_path)
        self.copy_all_btn.clicked.connect(self._copy_all)
        self.qr_only_chk.stateChanged.connect(
            lambda v: setattr(self.settings, "scan_qr_only", bool(v))
        )

    # ── Decode Logic ─────────────────────────────────────────────────── #

    def _decode_pil(self, img: Image.Image):
        try:
            if self.settings.scan_qr_only:
                return zbar_decode(img, symbols=[ZBarSymbol.QRCODE])
            return zbar_decode(img)
        except Exception as e:
            logging.error("pyzbar decode error", exc_info=True)
            return []

    def _open_image(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Image",
            filter="Images (*.png *.jpg *.jpeg *.gif *.bmp *.tif *.tiff *.webp)"
        )
        if path:
            self._decode_path(path)

    def _decode_path(self, path: str):
        try:
            img = Image.open(path)
            results = self._decode_pil(img)
            self.preview.set_pixmap(
                pil_to_qpixmap(img.convert("RGB"))
            )
            self._display_results(results, source=path)
        except Exception as e:
            show_error(self, "Decode Failed", str(e))

    def _display_results(self, results, source: str):
        # Clear previous results
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not results:
            self.status_chip.set("No codes detected", "warn")
            return

        self.status_chip.set(f"{len(results)} code{'s' if len(results) > 1 else ''} found", "success")

        for i, obj in enumerate(results, 1):
            t = getattr(obj, "type", "UNKNOWN")
            d = obj.data.decode("utf-8", errors="replace")
            card = ResultCard(i, t, d)
            card.copyRequested.connect(
                lambda text: QtWidgets.QApplication.clipboard().setText(text)
            )
            card.urlRequested.connect(
                lambda url: QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
            )
            self.results_layout.insertWidget(self.results_layout.count() - 1, card)

            if i == 1:
                self.decoded.emit(t, d, source)

    def _copy_all(self):
        texts = []
        for i in range(self.results_layout.count() - 1):
            widget = self.results_layout.itemAt(i).widget()
            if isinstance(widget, ResultCard):
                texts.append(widget.data)
        if texts:
            QtWidgets.QApplication.clipboard().setText("\n".join(texts))

    # ── Camera ───────────────────────────────────────────────────────── #

    def _toggle_camera(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(int(self.settings.camera_index))
            if not self.cap.isOpened():
                self.cap.release()
                self.cap = None
                show_error(self, "Camera Error", f"Could not open camera {self.settings.camera_index}.")
                return
            self.cam_btn.setText("Stop Camera")
            self.cam_btn.setStyleSheet("")  # revert to danger style
            self.cam_btn.setObjectName("dangerBtn")
            self.cam_btn.style().polish(self.cam_btn)
            self.timer.start()
            self.status_chip.set("Camera active", "info")
        else:
            self.stop_camera()

    def stop_camera(self):
        if self.cap:
            self.timer.stop()
            self.cap.release()
            self.cap = None
            self.cam_btn.setText("Start Camera")
            self.cam_btn.setObjectName("primaryBtn")
            self.cam_btn.style().polish(self.cam_btn)
            self.preview.clear("Camera feed stopped")
            self.status_chip.set("Camera stopped", "neutral")

    def _read_frame(self):
        if not self.cap:
            return
        ok, frame = self.cap.read()
        if not ok:
            return

        import cv2 as _cv2
        pil_img = Image.fromarray(_cv2.cvtColor(frame, _cv2.COLOR_BGR2RGB))
        results = self._decode_pil(pil_img)
        if results:
            self._display_results(results, source="camera")

        h, w, ch = frame.shape
        rgb = _cv2.cvtColor(frame, _cv2.COLOR_BGR2RGB)
        qimg = QtGui.QImage(rgb.data, w, h, ch * w, QtGui.QImage.Format.Format_RGB888)
        self.preview.set_pixmap(QtGui.QPixmap.fromImage(qimg))
