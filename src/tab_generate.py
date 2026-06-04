"""
QR Professional Suite — Generator Tab
Full-featured QR and barcode generator with live preview.
"""

import io
import os
import logging
from math import sqrt
from typing import Optional

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QStackedWidget
from PIL import Image, ImageFilter

import qrcode
import qrcode.constants
import barcode as barcode_lib
from barcode.writer import ImageWriter

from core import pil_to_qpixmap, show_error, show_info, AppSettings
from widgets import (
    ColorSwatch, PreviewPanel, SectionHeader, StatusChip, FormRow, Divider
)


class GeneratorTab(QtWidgets.QWidget):
    generated = QtCore.pyqtSignal(str, str, str)

    def __init__(self, settings: AppSettings):
        super().__init__()
        self.settings = settings
        self.logo_path: Optional[str] = None
        self.current_image: Optional[Image.Image] = None

        self._build_ui()
        self._connect_signals()
        self._on_type_changed(self.type_combo.currentText())

    # ── UI Construction ──────────────────────────────────────────────── #

    def _build_ui(self):
        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(20)

        # Left panel — controls
        left = QtWidgets.QWidget()
        left.setObjectName("panelFrame")
        left.setFixedWidth(360)
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(14)

        left_layout.addWidget(SectionHeader("Generator", "Create QR codes and barcodes"))
        left_layout.addWidget(Divider())

        # Code type
        type_label = QtWidgets.QLabel("CODE TYPE")
        type_label.setObjectName("sectionLabel")
        left_layout.addWidget(type_label)

        self.type_combo = QtWidgets.QComboBox()
        types = [
            "QR — Text / URL",
            "QR — Wi-Fi",
            "QR — vCard",
            "QR — E-mail",
            "QR — SMS",
            "QR — Phone",
            "QR — Geo Location",
            "QR — Bitcoin",
            "EAN-13",
            "Code 128",
            "Code 39",
            "UPC-A",
        ]
        self.type_combo.addItems(types)
        left_layout.addWidget(self.type_combo)

        # Input stack
        input_label = QtWidgets.QLabel("INPUT DATA")
        input_label.setObjectName("sectionLabel")
        left_layout.addWidget(input_label)

        self.input_stack = QStackedWidget()
        self._build_input_forms()
        left_layout.addWidget(self.input_stack)

        left_layout.addWidget(Divider())

        # Appearance
        appear_label = QtWidgets.QLabel("APPEARANCE")
        appear_label.setObjectName("sectionLabel")
        left_layout.addWidget(appear_label)

        # Colors
        color_row = QtWidgets.QHBoxLayout()
        color_row.setSpacing(8)
        self.fg_swatch = ColorSwatch(self.settings.default_fg, "Foreground")
        self.bg_swatch = ColorSwatch(self.settings.default_bg, "Background")
        fg_col = QtWidgets.QVBoxLayout()
        fg_col.setSpacing(3)
        fg_lbl = QtWidgets.QLabel("Foreground")
        fg_lbl.setStyleSheet("color: #6B7280; font-size: 10px;")
        fg_col.addWidget(fg_lbl)
        fg_col.addWidget(self.fg_swatch)
        bg_col = QtWidgets.QVBoxLayout()
        bg_col.setSpacing(3)
        bg_lbl = QtWidgets.QLabel("Background")
        bg_lbl.setStyleSheet("color: #6B7280; font-size: 10px;")
        bg_col.addWidget(bg_lbl)
        bg_col.addWidget(self.bg_swatch)
        color_row.addLayout(fg_col)
        color_row.addLayout(bg_col)
        color_row.addStretch(1)
        left_layout.addLayout(color_row)

        # Style
        style_row = QtWidgets.QHBoxLayout()
        style_row.setSpacing(8)
        style_lbl_widget = QtWidgets.QVBoxLayout()
        style_lbl_widget.setSpacing(3)
        grad_lbl = QtWidgets.QLabel("Gradient Style")
        grad_lbl.setStyleSheet("color: #6B7280; font-size: 10px;")
        self.gradient_mode = QtWidgets.QComboBox()
        self.gradient_mode.addItems(["Solid", "Vertical", "Horizontal", "Radial", "Diagonal"])
        style_lbl_widget.addWidget(grad_lbl)
        style_lbl_widget.addWidget(self.gradient_mode)

        ec_lbl_widget = QtWidgets.QVBoxLayout()
        ec_lbl_widget.setSpacing(3)
        ec_lbl = QtWidgets.QLabel("Error Correction")
        ec_lbl.setStyleSheet("color: #6B7280; font-size: 10px;")
        self.error_combo = QtWidgets.QComboBox()
        self.error_combo.addItems(["L (7%)", "M (15%)", "Q (25%)", "H (30%)"])
        self.error_combo.setCurrentIndex(3)
        ec_lbl_widget.addWidget(ec_lbl)
        ec_lbl_widget.addWidget(self.error_combo)

        style_row.addLayout(style_lbl_widget)
        style_row.addLayout(ec_lbl_widget)
        left_layout.addLayout(style_row)

        # Size
        size_row = QtWidgets.QHBoxLayout()
        size_row.setSpacing(8)
        size_lbl_col = QtWidgets.QVBoxLayout()
        size_lbl_col.setSpacing(3)
        size_lbl = QtWidgets.QLabel("Module Size")
        size_lbl.setStyleSheet("color: #6B7280; font-size: 10px;")
        self.size_spin = QtWidgets.QSpinBox()
        self.size_spin.setRange(4, 30)
        self.size_spin.setValue(self.settings.default_size)
        self.size_spin.setSuffix(" px")
        size_lbl_col.addWidget(size_lbl)
        size_lbl_col.addWidget(self.size_spin)

        border_lbl_col = QtWidgets.QVBoxLayout()
        border_lbl_col.setSpacing(3)
        border_lbl = QtWidgets.QLabel("Border (modules)")
        border_lbl.setStyleSheet("color: #6B7280; font-size: 10px;")
        self.border_spin = QtWidgets.QSpinBox()
        self.border_spin.setRange(0, 12)
        self.border_spin.setValue(self.settings.default_border)
        border_lbl_col.addWidget(border_lbl)
        border_lbl_col.addWidget(self.border_spin)

        size_row.addLayout(size_lbl_col)
        size_row.addLayout(border_lbl_col)
        left_layout.addLayout(size_row)

        # Corner radius (QR only)
        self.round_row = QtWidgets.QWidget()
        round_layout = QtWidgets.QVBoxLayout(self.round_row)
        round_layout.setContentsMargins(0, 0, 0, 0)
        round_layout.setSpacing(3)
        round_lbl = QtWidgets.QLabel("Module Rounding")
        round_lbl.setStyleSheet("color: #6B7280; font-size: 10px;")
        self.round_slider = QtWidgets.QSlider(Qt.Orientation.Horizontal)
        self.round_slider.setRange(0, 100)
        self.round_slider.setValue(0)
        self.round_slider.setToolTip("Round the QR module corners (0 = square, 100 = round)")
        round_layout.addWidget(round_lbl)
        round_layout.addWidget(self.round_slider)
        left_layout.addWidget(self.round_row)

        left_layout.addWidget(Divider())

        # Logo embed
        logo_label = QtWidgets.QLabel("LOGO / OVERLAY")
        logo_label.setObjectName("sectionLabel")
        left_layout.addWidget(logo_label)

        self.logo_section = QtWidgets.QWidget()
        logo_layout = QtWidgets.QHBoxLayout(self.logo_section)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(8)
        self.logo_btn = QtWidgets.QPushButton("Choose…")
        self.logo_btn.setFixedWidth(80)
        self.logo_clear_btn = QtWidgets.QPushButton("✕")
        self.logo_clear_btn.setFixedWidth(30)
        self.logo_clear_btn.setToolTip("Remove logo")
        self.logo_lbl = QtWidgets.QLabel("No logo selected")
        self.logo_lbl.setStyleSheet("color: #4B5563; font-size: 11px;")
        logo_layout.addWidget(self.logo_btn)
        logo_layout.addWidget(self.logo_clear_btn)
        logo_layout.addWidget(self.logo_lbl, 1)
        left_layout.addWidget(self.logo_section)

        left_layout.addStretch(1)
        left_layout.addWidget(Divider())

        # Status + buttons
        self.status_chip = StatusChip()
        left_layout.addWidget(self.status_chip)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(8)
        self.generate_btn = QtWidgets.QPushButton("Generate")
        self.generate_btn.setObjectName("primaryBtn")
        self.save_btn = QtWidgets.QPushButton("Save Image…")
        self.copy_btn = QtWidgets.QPushButton("Copy")
        btn_row.addWidget(self.generate_btn, 2)
        btn_row.addWidget(self.save_btn, 2)
        btn_row.addWidget(self.copy_btn, 1)
        left_layout.addLayout(btn_row)

        root.addWidget(left)

        # Right panel — preview
        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        preview_header = QtWidgets.QHBoxLayout()
        preview_title = QtWidgets.QLabel("PREVIEW")
        preview_title.setObjectName("sectionLabel")
        self.preview_info = QtWidgets.QLabel("")
        self.preview_info.setStyleSheet("color: #2A3042; font-size: 11px;")
        preview_header.addWidget(preview_title)
        preview_header.addStretch(1)
        preview_header.addWidget(self.preview_info)
        right_layout.addLayout(preview_header)

        self.preview = PreviewPanel("Generate a code to see a preview")
        right_layout.addWidget(self.preview, 1)

        root.addWidget(right, 1)

    def _build_input_forms(self):
        ec_map = {"L (7%)": qrcode.constants.ERROR_CORRECT_L,
                  "M (15%)": qrcode.constants.ERROR_CORRECT_M,
                  "Q (25%)": qrcode.constants.ERROR_CORRECT_Q,
                  "H (30%)": qrcode.constants.ERROR_CORRECT_H}

        def form(fields):
            w = QtWidgets.QWidget()
            layout = QtWidgets.QFormLayout(w)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(8)
            layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            widgets = {}
            for key, label, widget in fields:
                layout.addRow(label + ":", widget)
                widgets[key] = widget
            w._fields = widgets
            return w

        # Text/URL
        self.f_text = form([("data", "URL / Text",
            self._plain("https://example.com"))])
        self.input_stack.addWidget(self.f_text)
        self._type_map = {"QR — Text / URL": 0}

        # Wi-Fi
        self.f_wifi = form([
            ("ssid", "Network SSID", QtWidgets.QLineEdit()),
            ("pass", "Password", self._passwd()),
            ("enc",  "Encryption",  self._combo(["WPA/WPA2", "WEP", "None"])),
            ("hidden", "Hidden",    self._check("SSID is hidden")),
        ])
        self.input_stack.addWidget(self.f_wifi)
        self._type_map["QR — Wi-Fi"] = 1

        # vCard
        self.f_vcard = form([
            ("name",  "Full Name",  QtWidgets.QLineEdit("Jane Smith")),
            ("title", "Job Title",  QtWidgets.QLineEdit()),
            ("org",   "Company",    QtWidgets.QLineEdit()),
            ("phone", "Phone",      QtWidgets.QLineEdit("+61 400 000 000")),
            ("email", "E-mail",     QtWidgets.QLineEdit("jane@example.com")),
            ("url",   "Website",    QtWidgets.QLineEdit()),
            ("addr",  "Address",    QtWidgets.QLineEdit()),
        ])
        self.input_stack.addWidget(self.f_vcard)
        self._type_map["QR — vCard"] = 2

        # E-mail
        self.f_email = form([
            ("to",      "To",      QtWidgets.QLineEdit()),
            ("subject", "Subject", QtWidgets.QLineEdit()),
            ("body",    "Body",    self._plain("")),
        ])
        self.input_stack.addWidget(self.f_email)
        self._type_map["QR — E-mail"] = 3

        # SMS
        self.f_sms = form([
            ("num", "Phone Number", QtWidgets.QLineEdit("+61 400 000 000")),
            ("msg", "Message",      self._plain("Your message here.")),
        ])
        self.input_stack.addWidget(self.f_sms)
        self._type_map["QR — SMS"] = 4

        # Phone
        self.f_phone = form([("num", "Phone Number", QtWidgets.QLineEdit("+61 400 000 000"))])
        self.input_stack.addWidget(self.f_phone)
        self._type_map["QR — Phone"] = 5

        # Geo
        self.f_geo = form([
            ("lat", "Latitude",  QtWidgets.QLineEdit("-27.4705")),
            ("lon", "Longitude", QtWidgets.QLineEdit("153.0260")),
            ("alt", "Altitude",  QtWidgets.QLineEdit("0")),
        ])
        self.input_stack.addWidget(self.f_geo)
        self._type_map["QR — Geo Location"] = 6

        # Bitcoin
        self.f_btc = form([
            ("addr",   "Address",  QtWidgets.QLineEdit()),
            ("amount", "Amount",   QtWidgets.QLineEdit()),
            ("label",  "Label",    QtWidgets.QLineEdit()),
            ("msg",    "Message",  QtWidgets.QLineEdit()),
        ])
        self.input_stack.addWidget(self.f_btc)
        self._type_map["QR — Bitcoin"] = 7

        # 1D barcodes — shared text form
        self.f_barcode = form([("data", "Data / Number", QtWidgets.QLineEdit("012345678905"))])
        self.input_stack.addWidget(self.f_barcode)
        for t in ["EAN-13", "Code 128", "Code 39", "UPC-A"]:
            self._type_map[t] = 8

    # ── Helpers ──────────────────────────────────────────────────────── #

    def _plain(self, text=""):
        w = QtWidgets.QPlainTextEdit(text)
        w.setMaximumHeight(80)
        return w

    def _passwd(self):
        w = QtWidgets.QLineEdit()
        w.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        return w

    def _combo(self, items):
        w = QtWidgets.QComboBox()
        w.addItems(items)
        return w

    def _check(self, text):
        return QtWidgets.QCheckBox(text)

    # ── Signals ──────────────────────────────────────────────────────── #

    def _connect_signals(self):
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        self.logo_btn.clicked.connect(self._select_logo)
        self.logo_clear_btn.clicked.connect(self._clear_logo)
        self.generate_btn.clicked.connect(self._generate)
        self.save_btn.clicked.connect(self._save)
        self.copy_btn.clicked.connect(self._copy)

    def _on_type_changed(self, text: str):
        idx = self._type_map.get(text, 0)
        self.input_stack.setCurrentIndex(idx)
        is_qr = text.startswith("QR")
        self.logo_section.setVisible(is_qr)
        self.round_row.setVisible(is_qr)
        self.error_combo.setEnabled(is_qr)

    def _select_logo(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Logo Image",
            filter="Images (*.png *.jpg *.jpeg *.gif *.bmp *.svg *.webp)"
        )
        if path:
            self.logo_path = path
            self.logo_lbl.setText(os.path.basename(path))
            self.logo_lbl.setStyleSheet("color: #60A5FA; font-size: 11px;")
        self.status_chip.hide_chip()

    def _clear_logo(self):
        self.logo_path = None
        self.logo_lbl.setText("No logo selected")
        self.logo_lbl.setStyleSheet("color: #4B5563; font-size: 11px;")

    # ── Payload Construction ─────────────────────────────────────────── #

    def _get_payload(self) -> tuple[str, str]:
        t = self.type_combo.currentText()
        f = self.f_text._fields if t == "QR — Text / URL" else {}

        if t == "QR — Text / URL":
            d = self.f_text._fields["data"].toPlainText().strip()
            if not d:
                raise ValueError("Data cannot be empty.")
            return d, d

        if t == "QR — Wi-Fi":
            F = self.f_wifi._fields
            ssid = F["ssid"].text().strip()
            pwd = F["pass"].text().strip()
            enc = F["enc"].currentText().split("/")[0]
            if enc == "None": enc = "nopass"
            hidden = ";H:true" if F["hidden"].isChecked() else ""
            if not ssid: raise ValueError("SSID cannot be empty.")
            return f"WIFI:T:{enc};S:{ssid};P:{pwd}{hidden};;", f"Wi-Fi: {ssid}"

        if t == "QR — vCard":
            F = self.f_vcard._fields
            name = F["name"].text().strip()
            if not name: raise ValueError("Name cannot be empty.")
            lines = ["BEGIN:VCARD", "VERSION:3.0", f"FN:{name}", f"N:{name}"]
            for key, tag in [("title","TITLE"),("org","ORG"),("phone","TEL"),
                              ("email","EMAIL"),("url","URL"),("addr","ADR")]:
                val = F[key].text().strip()
                if val: lines.append(f"{tag}:{val}")
            lines.append("END:VCARD")
            return "\n".join(lines), f"vCard: {name}"

        if t == "QR — E-mail":
            F = self.f_email._fields
            to = F["to"].text().strip()
            sub = F["subject"].text().strip()
            body = F["body"].toPlainText().strip()
            if not to: raise ValueError("Recipient address cannot be empty.")
            payload = f"MATMSG:TO:{to};SUB:{sub};BODY:{body};;"
            return payload, f"Email to: {to}"

        if t == "QR — SMS":
            F = self.f_sms._fields
            num = F["num"].text().strip()
            msg = F["msg"].toPlainText().strip()
            if not num: raise ValueError("Phone number cannot be empty.")
            return f"SMSTO:{num}:{msg}", f"SMS: {num}"

        if t == "QR — Phone":
            num = self.f_phone._fields["num"].text().strip()
            if not num: raise ValueError("Phone number cannot be empty.")
            return f"tel:{num}", f"Phone: {num}"

        if t == "QR — Geo Location":
            F = self.f_geo._fields
            lat, lon, alt = F["lat"].text().strip(), F["lon"].text().strip(), F["alt"].text().strip()
            if not lat or not lon: raise ValueError("Lat/Lon cannot be empty.")
            return f"geo:{lat},{lon},{alt}", f"Geo: {lat}, {lon}"

        if t == "QR — Bitcoin":
            F = self.f_btc._fields
            addr = F["addr"].text().strip()
            if not addr: raise ValueError("Bitcoin address cannot be empty.")
            parts = [f"bitcoin:{addr}"]
            params = []
            if F["amount"].text().strip(): params.append(f"amount={F['amount'].text().strip()}")
            if F["label"].text().strip(): params.append(f"label={F['label'].text().strip()}")
            if F["msg"].text().strip(): params.append(f"message={F['msg'].text().strip()}")
            if params: parts.append("?" + "&".join(params))
            return "".join(parts), f"BTC: {addr[:12]}…"

        # 1D barcodes
        d = self.f_barcode._fields["data"].text().strip()
        if not d: raise ValueError("Barcode data cannot be empty.")
        return d, d

    # ── Generation ──────────────────────────────────────────────────── #

    def _ec_constant(self):
        ec_map = {
            "L (7%)":  qrcode.constants.ERROR_CORRECT_L,
            "M (15%)": qrcode.constants.ERROR_CORRECT_M,
            "Q (25%)": qrcode.constants.ERROR_CORRECT_Q,
            "H (30%)": qrcode.constants.ERROR_CORRECT_H,
        }
        return ec_map.get(self.error_combo.currentText(), qrcode.constants.ERROR_CORRECT_H)

    def _generate(self):
        code_type = self.type_combo.currentText()
        try:
            payload, display_data = self._get_payload()
            if code_type.startswith("QR"):
                img = self._make_qr(payload)
                if self.logo_path:
                    img = self._apply_logo(img)
            else:
                img = self._make_barcode(payload, code_type)

            self.current_image = img
            self.preview.set_pixmap(pil_to_qpixmap(img))
            w, h = img.size
            self.preview_info.setText(f"{w} × {h} px")
            self.status_chip.set("Generated successfully", "success")
            logging.info(f"Generated {code_type}: {display_data[:60]}")

        except Exception as e:
            logging.error("Generation failed", exc_info=True)
            self.status_chip.set(str(e), "error")
            show_error(self, "Generation Failed", str(e))

    def _make_qr(self, payload: str) -> Image.Image:
        qr = qrcode.QRCode(
            error_correction=self._ec_constant(),
            box_size=self.size_spin.value(),
            border=self.border_spin.value()
        )
        qr.add_data(payload)
        qr.make(fit=True)

        fg = self.fg_swatch.color().getRgb()[:3]
        bg = self.bg_swatch.color().getRgb()[:3]
        mode = self.gradient_mode.currentText()

        if mode == "Solid":
            return qr.make_image(fill_color=fg, back_color=bg).convert("RGB")

        img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
        w, h = img.size
        pixels = img.load()

        for y in range(h):
            for x in range(w):
                if mode == "Vertical":       t = y / h
                elif mode == "Horizontal":   t = x / w
                elif mode == "Diagonal":     t = (x + y) / (w + h)
                else:  # Radial
                    cx, cy = w / 2, h / 2
                    dist = sqrt((x - cx)**2 + (y - cy)**2)
                    t = min(1.0, dist / sqrt(cx**2 + cy**2))

                r = int(fg[0] * (1 - t) + bg[0] * t)
                g = int(fg[1] * (1 - t) + bg[1] * t)
                b = int(fg[2] * (1 - t) + bg[2] * t)

                if pixels[x, y][0] < 128:
                    pixels[x, y] = (r, g, b, 255)
                else:
                    pixels[x, y] = (bg[0], bg[1], bg[2], 255)

        return img.convert("RGB")

    def _make_barcode(self, data: str, code_type: str) -> Image.Image:
        type_map = {
            "EAN-13":   "ean13",
            "Code 128": "code128",
            "Code 39":  "code39",
            "UPC-A":    "upca",
        }
        cls_name = type_map.get(code_type, "code128")
        try:
            BarcodeClass = barcode_lib.get_barcode_class(cls_name)
        except Exception:
            raise RuntimeError(f"Barcode type '{code_type}' not supported.")
        buf = io.BytesIO()
        BarcodeClass(data, writer=ImageWriter()).write(buf)
        buf.seek(0)
        return Image.open(buf).convert("RGB")

    def _apply_logo(self, base_img: Image.Image) -> Image.Image:
        try:
            logo = Image.open(self.logo_path).convert("RGBA")
            base = base_img.convert("RGBA")
            lw = max(40, base.width // 4)
            ratio = lw / max(1, logo.width)
            logo = logo.resize((lw, int(logo.height * ratio)), Image.Resampling.LANCZOS)
            # White backing circle
            pad = 8
            backing = Image.new("RGBA", (logo.width + pad * 2, logo.height + pad * 2), (255, 255, 255, 255))
            backing.alpha_composite(logo, (pad, pad))
            x = (base.width - backing.width) // 2
            y = (base.height - backing.height) // 2
            base.alpha_composite(backing, (x, y))
            return base.convert("RGB")
        except Exception as ex:
            show_error(self, "Logo Error", str(ex))
            return base_img.convert("RGB")

    # ── Save / Copy ──────────────────────────────────────────────────── #

    def _save(self):
        if not self.current_image:
            self.status_chip.set("Generate a code first", "warn")
            return
        out, sel_filter = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Image",
            filter="PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;BMP Image (*.bmp)"
        )
        if out:
            try:
                fmt = "PNG"
                if out.lower().endswith((".jpg", ".jpeg")):
                    fmt = "JPEG"
                elif out.lower().endswith(".bmp"):
                    fmt = "BMP"
                save_img = self.current_image.convert("RGB") if fmt == "JPEG" else self.current_image
                save_img.save(out, fmt)
                _, display_data = self._get_payload()
                self.generated.emit(self.type_combo.currentText(), display_data, out)
                self.status_chip.set(f"Saved → {os.path.basename(out)}", "success")
            except Exception as e:
                show_error(self, "Save Failed", str(e))

    def _copy(self):
        if not self.current_image:
            self.status_chip.set("Nothing to copy", "warn")
            return
        pix = pil_to_qpixmap(self.current_image)
        QtWidgets.QApplication.clipboard().setPixmap(pix)
        self.status_chip.set("Copied to clipboard", "info")
