"""
QR Professional Suite — Batch Tab
High-volume generate and decode operations.
"""

import os
import io
import csv
import time
import logging
import threading
from typing import List

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import Qt
from PIL import Image

import qrcode
import qrcode.constants
import barcode as barcode_lib
from barcode.writer import ImageWriter
from pyzbar.pyzbar import decode as zbar_decode

from core import HistoryItem, show_info, show_error
from widgets import SectionHeader, Divider, StatusChip


class BatchWorker(QtCore.QThread):
    progress = QtCore.pyqtSignal(int, int, str)
    finished = QtCore.pyqtSignal(list)

    def __init__(self, task: str, data):
        super().__init__()
        self.task = task
        self.data = data

    def run(self):
        items: List[HistoryItem] = []
        if self.task == "generate":
            rows = self.data["rows"]
            out_dir = self.data["out_dir"]
            for i, row in enumerate(rows, 1):
                data = row.get("data", "").strip()
                code_type = row.get("type", "QR Code").strip() or "QR Code"
                filename = row.get("filename", "").strip()
                if not data:
                    continue
                if not filename:
                    filename = f"code_{i}.png"
                out_path = os.path.join(out_dir, filename)
                self.progress.emit(i, len(rows), f"Generating {filename}…")
                try:
                    if code_type.lower().startswith("qr"):
                        qr = qrcode.QRCode(
                            error_correction=qrcode.constants.ERROR_CORRECT_M,
                            box_size=10, border=4
                        )
                        qr.add_data(data)
                        qr.make(fit=True)
                        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
                    else:
                        type_map = {"ean-13":"ean13","code 128":"code128","code 39":"code39","upca":"upca"}
                        cls_name = type_map.get(code_type.lower(), "code128")
                        BarcodeClass = barcode_lib.get_barcode_class(cls_name)
                        buf = io.BytesIO()
                        BarcodeClass(data, writer=ImageWriter()).write(buf)
                        buf.seek(0)
                        img = Image.open(buf).convert("RGB")
                    os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else ".", exist_ok=True)
                    img.save(out_path)
                    items.append(HistoryItem(time.time(), "generate", code_type, data, "batch", out_path))
                except Exception as e:
                    items.append(HistoryItem(time.time(), "generate", code_type, f"ERROR: {e}", "batch", out_path))
                    logging.error(f"Batch generate error row {i}: {e}")

        elif self.task == "decode":
            paths = self.data["paths"]
            for i, path in enumerate(paths, 1):
                self.progress.emit(i, len(paths), f"Decoding {os.path.basename(path)}…")
                try:
                    results = zbar_decode(Image.open(path))
                    if results:
                        for r in results:
                            t = getattr(r, "type", "UNKNOWN")
                            d = r.data.decode("utf-8", errors="replace")
                            items.append(HistoryItem(time.time(), "decode", t, d, path, ""))
                    else:
                        items.append(HistoryItem(time.time(), "decode", "N/A", "NO CODE FOUND", path, ""))
                except Exception as e:
                    items.append(HistoryItem(time.time(), "decode", "ERROR", str(e), path, ""))
                    logging.error(f"Batch decode error {path}: {e}")

        self.finished.emit(items)


class BatchTab(QtWidgets.QWidget):
    generated_many = QtCore.pyqtSignal(list)
    decoded_many = QtCore.pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self._worker = None
        self._build_ui()

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(20)

        root.addWidget(SectionHeader("Batch Operations", "Process multiple codes at once"))
        root.addWidget(Divider())

        # Two column layout
        cols = QtWidgets.QHBoxLayout()
        cols.setSpacing(20)

        # ── Generate Column ──────────────────────────────────────────── #
        gen_group = QtWidgets.QGroupBox("Batch Generate from CSV")
        gen_layout = QtWidgets.QVBoxLayout(gen_group)
        gen_layout.setSpacing(10)

        gen_info = QtWidgets.QLabel(
            "CSV format: data, type, filename\n"
            "Supported types: QR Code, EAN-13, Code 128, Code 39, UPC-A"
        )
        gen_info.setStyleSheet("color: #4B5563; font-size: 11px; line-height: 1.6;")
        gen_layout.addWidget(gen_info)

        csv_row = QtWidgets.QHBoxLayout()
        self.csv_edit = QtWidgets.QLineEdit()
        self.csv_edit.setPlaceholderText("Select a .csv file…")
        self.csv_browse = QtWidgets.QPushButton("Browse…")
        csv_row.addWidget(self.csv_edit, 1)
        csv_row.addWidget(self.csv_browse)
        gen_layout.addLayout(csv_row)

        dir_row = QtWidgets.QHBoxLayout()
        self.outdir_edit = QtWidgets.QLineEdit()
        self.outdir_edit.setPlaceholderText("Output folder…")
        self.outdir_browse = QtWidgets.QPushButton("Browse…")
        dir_row.addWidget(self.outdir_edit, 1)
        dir_row.addWidget(self.outdir_browse)
        gen_layout.addLayout(dir_row)

        # Template download
        template_btn = QtWidgets.QPushButton("Download CSV Template")
        template_btn.setStyleSheet("color: #60A5FA; background: transparent; border: none; text-align: left;")
        gen_layout.addWidget(template_btn)

        self.gen_run_btn = QtWidgets.QPushButton("Generate All Codes")
        self.gen_run_btn.setObjectName("primaryBtn")
        gen_layout.addWidget(self.gen_run_btn)

        cols.addWidget(gen_group)

        # ── Decode Column ────────────────────────────────────────────── #
        dec_group = QtWidgets.QGroupBox("Batch Decode from Folder")
        dec_layout = QtWidgets.QVBoxLayout(dec_group)
        dec_layout.setSpacing(10)

        dec_info = QtWidgets.QLabel(
            "Select a folder containing image files.\n"
            "All PNG, JPG, GIF, BMP, TIFF files will be scanned."
        )
        dec_info.setStyleSheet("color: #4B5563; font-size: 11px; line-height: 1.6;")
        dec_layout.addWidget(dec_info)

        folder_row = QtWidgets.QHBoxLayout()
        self.folder_edit = QtWidgets.QLineEdit()
        self.folder_edit.setPlaceholderText("Select a folder…")
        self.folder_browse = QtWidgets.QPushButton("Browse…")
        folder_row.addWidget(self.folder_edit, 1)
        folder_row.addWidget(self.folder_browse)
        dec_layout.addLayout(folder_row)

        # Options
        self.recursive_chk = QtWidgets.QCheckBox("Scan subfolders recursively")
        dec_layout.addWidget(self.recursive_chk)

        self.export_csv_chk = QtWidgets.QCheckBox("Export results to CSV automatically")
        dec_layout.addWidget(self.export_csv_chk)

        dec_layout.addStretch(1)

        self.dec_run_btn = QtWidgets.QPushButton("Decode All Images")
        self.dec_run_btn.setObjectName("primaryBtn")
        dec_layout.addWidget(self.dec_run_btn)

        cols.addWidget(dec_group)
        root.addLayout(cols)

        # ── Progress ─────────────────────────────────────────────────── #
        self.status_chip = StatusChip()
        root.addWidget(self.status_chip)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        root.addWidget(self.progress_bar)

        self.progress_lbl = QtWidgets.QLabel("")
        self.progress_lbl.setStyleSheet("color: #4B5563; font-size: 11px;")
        self.progress_lbl.setVisible(False)
        root.addWidget(self.progress_lbl)

        # ── Results Preview ───────────────────────────────────────────── #
        results_label = QtWidgets.QLabel("RESULTS LOG")
        results_label.setObjectName("sectionLabel")
        root.addWidget(results_label)

        self.results_text = QtWidgets.QPlainTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlaceholderText("Batch operation results will appear here…")
        self.results_text.setMaximumHeight(180)
        root.addWidget(self.results_text)

        root.addStretch(1)

        # ── Connect ───────────────────────────────────────────────────── #
        self.csv_browse.clicked.connect(self._pick_csv)
        self.outdir_browse.clicked.connect(self._pick_outdir)
        self.folder_browse.clicked.connect(self._pick_folder)
        self.gen_run_btn.clicked.connect(self._run_generate)
        self.dec_run_btn.clicked.connect(self._run_decode)
        template_btn.clicked.connect(self._save_template)

    def _pick_csv(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select CSV", filter="CSV (*.csv)")
        if path:
            self.csv_edit.setText(path)

    def _pick_outdir(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if path:
            self.outdir_edit.setText(path)

    def _pick_folder(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if path:
            self.folder_edit.setText(path)

    def _save_template(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save CSV Template", "batch_template.csv", filter="CSV (*.csv)"
        )
        if path:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["data", "type", "filename"])
                w.writerow(["https://example.com", "QR Code", "example_qr.png"])
                w.writerow(["012345678905", "EAN-13", "barcode_ean.png"])
                w.writerow(["HELLO WORLD", "Code 128", "barcode128.png"])
            show_info(self, "Template Saved", f"CSV template saved to:\n{path}")

    def _run_generate(self):
        csv_path = self.csv_edit.text().strip()
        out_dir = self.outdir_edit.text().strip()
        if not csv_path:
            self.status_chip.set("Please select a CSV file", "warn")
            return
        if not out_dir:
            self.status_chip.set("Please select an output folder", "warn")
            return
        try:
            rows = []
            with open(csv_path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    rows.append(row)
            if not rows:
                self.status_chip.set("CSV file is empty or has no rows", "warn")
                return
        except Exception as e:
            show_error(self, "CSV Error", str(e))
            return

        self._start_worker("generate", {"rows": rows, "out_dir": out_dir})

    def _run_decode(self):
        folder = self.folder_edit.text().strip()
        if not folder:
            self.status_chip.set("Please select a folder", "warn")
            return

        exts = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp"}
        paths = []
        if self.recursive_chk.isChecked():
            for root, _, files in os.walk(folder):
                for name in files:
                    if os.path.splitext(name)[1].lower() in exts:
                        paths.append(os.path.join(root, name))
        else:
            for name in os.listdir(folder):
                fp = os.path.join(folder, name)
                if os.path.isfile(fp) and os.path.splitext(name)[1].lower() in exts:
                    paths.append(fp)

        if not paths:
            self.status_chip.set("No image files found in folder", "warn")
            return

        self._start_worker("decode", {"paths": paths})

    def _start_worker(self, task: str, data):
        self.gen_run_btn.setEnabled(False)
        self.dec_run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_lbl.setVisible(True)
        self.results_text.clear()
        self.status_chip.set("Processing…", "info")

        self._worker = BatchWorker(task, data)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, current: int, total: int, msg: str):
        pct = int(current / total * 100)
        self.progress_bar.setValue(pct)
        self.progress_lbl.setText(f"[{current}/{total}] {msg}")

    def _on_finished(self, items: List[HistoryItem]):
        self.gen_run_btn.setEnabled(True)
        self.dec_run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_lbl.setVisible(False)

        errors = [it for it in items if it.data.startswith("ERROR")]
        no_code = [it for it in items if it.data == "NO CODE FOUND"]
        ok = len(items) - len(errors) - len(no_code)

        summary_lines = [
            f"Completed: {len(items)} items processed",
            f"  ✓ Success: {ok}",
        ]
        if no_code:
            summary_lines.append(f"  ○ No code: {len(no_code)}")
        if errors:
            summary_lines.append(f"  ✗ Errors: {len(errors)}")
        summary_lines.append("")

        for it in items:
            icon = "✓" if not it.data.startswith("ERROR") and it.data != "NO CODE FOUND" else "✗"
            summary_lines.append(f"  {icon}  {os.path.basename(it.source or it.output)} → {it.data[:80]}")

        self.results_text.setPlainText("\n".join(summary_lines))

        if errors:
            self.status_chip.set(f"Done with {len(errors)} error(s)", "warn")
        else:
            self.status_chip.set(f"All {len(items)} items processed", "success")

        if items:
            action = items[0].action
            if action == "generate":
                self.generated_many.emit(items)
            else:
                self.decoded_many.emit(items)

        # Auto-export CSV
        if self.export_csv_chk.isChecked() and items:
            folder = self.folder_edit.text().strip() or os.path.expanduser("~")
            out_csv = os.path.join(folder, "batch_results.csv")
            try:
                with open(out_csv, "w", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    w.writerow(["timestamp", "action", "type", "data", "source", "output"])
                    import time as _time
                    for it in items:
                        w.writerow([
                            _time.strftime("%Y-%m-%d %H:%M:%S", _time.localtime(it.timestamp)),
                            it.action, it.code_type, it.data, it.source, it.output
                        ])
                self.status_chip.set(f"Results exported to {os.path.basename(out_csv)}", "success")
            except Exception as e:
                logging.warning(f"Auto-export failed: {e}")
