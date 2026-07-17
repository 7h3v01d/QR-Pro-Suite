import os

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QMimeData, QUrl, QPointF
from PyQt6.QtGui import QDropEvent, QColor

from widgets import ColorSwatch, StatusChip, DropZone, PreviewPanel, Divider, SectionHeader, FormRow


class TestColorSwatch:
    def test_initial_color(self, qapp):
        swatch = ColorSwatch(initial_hex="#336699", label="Foreground")
        assert swatch.hex() == "#336699"
        assert swatch.color() == QColor("#336699")
        assert swatch.text() == "#336699".upper()

    def test_set_color_updates_state(self, qapp):
        swatch = ColorSwatch()
        swatch.set_color("#ABCDEF")
        assert swatch.hex() == "#abcdef"
        assert swatch.text() == "#ABCDEF"

    def test_tooltip_reflects_label_and_color(self, qapp):
        swatch = ColorSwatch(initial_hex="#000000", label="BG")
        assert "BG" in swatch.toolTip()
        assert "#000000" in swatch.toolTip()

    def test_dark_color_uses_white_text(self, qapp):
        swatch = ColorSwatch(initial_hex="#000000")
        assert "color: #FFFFFF" in swatch.styleSheet()

    def test_light_color_uses_black_text(self, qapp):
        swatch = ColorSwatch(initial_hex="#FFFFFF")
        assert "color: #000000" in swatch.styleSheet()


class TestStatusChip:
    def test_hidden_initially(self, qapp):
        chip = StatusChip()
        assert chip.isVisible() is False

    def test_set_makes_visible_with_icon_prefix(self, qapp):
        chip = StatusChip()
        chip.set("All good", "success")
        assert chip.isVisible() is True
        assert chip.text() == "✓ All good"

    def test_set_unknown_kind_falls_back_to_info_style(self, qapp):
        chip = StatusChip()
        chip.set("msg", "totally-invalid-kind")
        assert chip.text() == "● msg"

    def test_hide_chip(self, qapp):
        chip = StatusChip()
        chip.set("visible now")
        chip.hide_chip()
        assert chip.isVisible() is False


class TestDropZone:
    def test_default_text(self, qapp):
        dz = DropZone()
        assert "Drop an image" in dz.text()

    def test_accepts_drops_enabled(self, qapp):
        dz = DropZone()
        assert dz.acceptDrops() is True

    def test_drop_event_with_valid_file_emits_signal(self, qapp, tmp_path):
        f = tmp_path / "img.png"
        f.write_bytes(b"fake png bytes")

        dz = DropZone()
        received = {}
        dz.fileDropped.connect(lambda path: received.setdefault("path", path))

        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(f))])
        event = QDropEvent(
            QPointF(0, 0), QtCore.Qt.DropAction.CopyAction, mime,
            QtCore.Qt.MouseButton.LeftButton, QtCore.Qt.KeyboardModifier.NoModifier
        )
        dz.dropEvent(event)

        assert received["path"] == str(f)

    def test_drop_event_with_nonexistent_file_does_not_emit(self, qapp):
        dz = DropZone()
        received = {}
        dz.fileDropped.connect(lambda path: received.setdefault("path", path))

        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile("/no/such/file.png")])
        event = QDropEvent(
            QPointF(0, 0), QtCore.Qt.DropAction.CopyAction, mime,
            QtCore.Qt.MouseButton.LeftButton, QtCore.Qt.KeyboardModifier.NoModifier
        )
        dz.dropEvent(event)

        assert "path" not in received


class TestPreviewPanel:
    def test_clear_with_explicit_text(self, qapp):
        panel = PreviewPanel(placeholder="nothing yet")
        panel.clear("nothing yet")
        assert panel._label.text() == "nothing yet"
        assert panel._pixmap is None

    def test_clear_default_text(self, qapp):
        # clear() with no args falls back to its own default, not the
        # placeholder passed to the constructor.
        panel = PreviewPanel(placeholder="custom placeholder")
        panel.clear()
        assert panel._label.text() == "No image generated yet"
        assert panel._pixmap is None

    def test_set_pixmap_stores_pixmap(self, qapp):
        panel = PreviewPanel()
        pix = QtGui.QPixmap(50, 50)
        pix.fill(QColor("red"))
        panel.resize(200, 200)
        panel.set_pixmap(pix)
        assert panel._pixmap is pix


class TestMiscWidgets:
    def test_divider_is_horizontal_line(self, qapp):
        d = Divider()
        assert d.frameShape() == QtWidgets.QFrame.Shape.HLine

    def test_section_header_shows_title_and_subtitle(self, qapp):
        header = SectionHeader("Title", "Subtitle text")
        labels = header.findChildren(QtWidgets.QLabel)
        texts = [lbl.text() for lbl in labels]
        assert "Title" in texts
        assert "Subtitle text" in texts

    def test_section_header_omits_subtitle_label_when_blank(self, qapp):
        header = SectionHeader("Only Title")
        labels = header.findChildren(QtWidgets.QLabel)
        assert len(labels) == 1
        assert labels[0].text() == "Only Title"

    def test_form_row_label_fixed_width(self, qapp):
        row = FormRow("My Label", QtWidgets.QLineEdit())
        label = row.findChild(QtWidgets.QLabel)
        assert label.text() == "My Label"
        assert label.width() == 130
