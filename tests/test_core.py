import json
import time

import pytest
from PIL import Image
from PyQt6 import QtCore, QtGui

from core import AppSettings, HistoryItem, HistoryModel, pil_to_qpixmap


# ─────────────────────────── AppSettings ─────────────────────────────── #

class TestAppSettings:
    def test_defaults(self):
        s = AppSettings()
        assert s.dark_theme is True
        assert s.camera_index == 0
        assert s.scan_qr_only is False
        assert s.default_fg == "#000000"
        assert s.default_bg == "#FFFFFF"
        assert s.default_size == 10
        assert s.default_border == 4
        assert s.default_error_correction == "H"
        assert s.recent_paths == []
        assert s.always_on_top is False

    def test_save_writes_json_file(self, tmp_path):
        s = AppSettings(camera_index=2, default_size=15)
        s.save()
        f = tmp_path / AppSettings.SETTINGS_FILE
        assert f.exists()
        data = json.loads(f.read_text())
        assert data["camera_index"] == 2
        assert data["default_size"] == 15
        # class-level constant should not leak into the saved dict
        assert "SETTINGS_FILE" not in data

    def test_load_restores_values(self, tmp_path):
        original = AppSettings(camera_index=3, default_bg="#123456", scan_qr_only=True)
        original.save()

        loaded = AppSettings().load()
        assert loaded.camera_index == 3
        assert loaded.default_bg == "#123456"
        assert loaded.scan_qr_only is True

    def test_load_missing_file_is_noop(self, tmp_path):
        s = AppSettings()
        result = s.load()
        assert result is s
        assert s.camera_index == 0  # still defaults

    def test_load_ignores_unknown_keys(self, tmp_path):
        f = tmp_path / AppSettings.SETTINGS_FILE
        f.write_text(json.dumps({"camera_index": 5, "totally_unknown_field": "x"}))
        s = AppSettings().load()
        assert s.camera_index == 5
        assert not hasattr(s, "totally_unknown_field")

    def test_load_corrupt_file_does_not_raise(self, tmp_path):
        f = tmp_path / AppSettings.SETTINGS_FILE
        f.write_text("{not valid json")
        s = AppSettings()
        result = s.load()  # should swallow the exception, not raise
        assert result is s
        assert s.camera_index == 0

    def test_recent_paths_round_trip(self, tmp_path):
        s = AppSettings(recent_paths=["/a.png", "/b.png"])
        s.save()
        loaded = AppSettings().load()
        assert loaded.recent_paths == ["/a.png", "/b.png"]


# ─────────────────────────── HistoryModel ────────────────────────────── #

def make_item(action="generate", code_type="QR — Text / URL", data="hello", source="ui", output="out.png", ts=None):
    return HistoryItem(
        timestamp=ts if ts is not None else time.time(),
        action=action, code_type=code_type, data=data, source=source, output=output,
    )


class TestHistoryModel:
    def test_starts_empty(self):
        model = HistoryModel()
        assert model.rowCount() == 0
        assert model.columnCount() == 6

    def test_add_inserts_at_front(self):
        model = HistoryModel()
        first = make_item(data="first")
        second = make_item(data="second")
        model.add(first)
        model.add(second)
        assert model.rowCount() == 2
        # most recently added item should be row 0
        assert model.items[0] is second
        assert model.items[1] is first

    def test_clear_empties_model(self):
        model = HistoryModel([make_item(), make_item()])
        assert model.rowCount() == 2
        model.clear()
        assert model.rowCount() == 0

    def test_headers(self):
        model = HistoryModel()
        assert model.headerData(0, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole) == "Time"
        assert model.headerData(1, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole) == "Action"
        # vertical orientation / wrong role returns None
        assert model.headerData(0, QtCore.Qt.Orientation.Vertical, QtCore.Qt.ItemDataRole.DisplayRole) is None

    def test_data_display_role(self):
        item = make_item(action="decode", code_type="QRCODE", data="hi there", source="cam", output="")
        model = HistoryModel([item])
        idx = model.index(0, 1)
        assert model.data(idx, QtCore.Qt.ItemDataRole.DisplayRole) == "DECODE"
        idx_type = model.index(0, 2)
        assert model.data(idx_type, QtCore.Qt.ItemDataRole.DisplayRole) == "QRCODE"

    def test_data_truncates_long_strings(self):
        long_data = "x" * 200
        item = make_item(data=long_data)
        model = HistoryModel([item])
        idx = model.index(0, 3)
        displayed = model.data(idx, QtCore.Qt.ItemDataRole.DisplayRole)
        assert len(displayed) == 118  # 117 chars + ellipsis
        assert displayed.endswith("…")

    def test_data_short_strings_not_truncated(self):
        item = make_item(data="short")
        model = HistoryModel([item])
        idx = model.index(0, 3)
        assert model.data(idx, QtCore.Qt.ItemDataRole.DisplayRole) == "short"

    def test_data_invalid_index_returns_none(self):
        model = HistoryModel([make_item()])
        assert model.data(QtCore.QModelIndex(), QtCore.Qt.ItemDataRole.DisplayRole) is None

    def test_foreground_role_colors(self):
        gen_item = make_item(action="generate")
        dec_item = make_item(action="decode")
        model = HistoryModel([gen_item, dec_item])

        gen_color = model.data(model.index(0, 1), QtCore.Qt.ItemDataRole.ForegroundRole)
        dec_color = model.data(model.index(1, 1), QtCore.Qt.ItemDataRole.ForegroundRole)

        assert isinstance(gen_color, QtGui.QColor)
        assert isinstance(dec_color, QtGui.QColor)
        assert gen_color != dec_color

    def test_export_csv(self, tmp_path):
        model = HistoryModel([
            make_item(action="generate", code_type="QR", data="a,b", source="s", output="o1"),
            make_item(action="decode", code_type="EAN13", data="123", source="s2", output="o2"),
        ])
        out = tmp_path / "history.csv"
        model.export_csv(str(out))

        content = out.read_text(encoding="utf-8")
        lines = content.strip().splitlines()
        assert lines[0] == "Time,Action,Type,Data,Source,Output"
        # csv module quotes fields containing commas
        assert '"a,b"' in content
        assert "123" in content
        assert len(lines) == 3  # header + 2 rows


# ─────────────────────────── pil_to_qpixmap ──────────────────────────── #

class TestPilToQPixmap:
    def test_converts_rgb_image(self, qapp):
        img = Image.new("RGB", (10, 20), color=(255, 0, 0))
        pix = pil_to_qpixmap(img)
        assert not pix.isNull()
        assert pix.width() == 10
        assert pix.height() == 20

    def test_converts_rgba_image(self, qapp):
        img = Image.new("RGBA", (5, 5), color=(0, 255, 0, 128))
        pix = pil_to_qpixmap(img)
        assert not pix.isNull()
        assert pix.width() == 5

    def test_converts_palette_image(self, qapp):
        img = Image.new("P", (8, 8))
        pix = pil_to_qpixmap(img)
        assert not pix.isNull()

    def test_rejects_non_pil_image(self, qapp):
        with pytest.raises(ValueError):
            pil_to_qpixmap("not an image")

    def test_rejects_zero_sized_image(self, qapp):
        img = Image.new("RGB", (0, 0))
        with pytest.raises(ValueError):
            pil_to_qpixmap(img)
