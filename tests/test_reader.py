import qrcode
import pytest
from PIL import Image

from core import AppSettings
from tab_reader import ReaderTab


@pytest.fixture
def reader_tab(qapp):
    return ReaderTab(AppSettings())


def make_qr_image(payload="reader test"):
    qr = qrcode.QRCode(border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def make_barcode_image(data="012345678905"):
    import io
    import barcode as barcode_lib
    from barcode.writer import ImageWriter
    BarcodeClass = barcode_lib.get_barcode_class("ean13")
    buf = io.BytesIO()
    BarcodeClass(data, writer=ImageWriter()).write(buf)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


class TestDecodePil:
    def test_decodes_qr_code(self, reader_tab):
        img = make_qr_image("hello reader")
        results = reader_tab._decode_pil(img)
        assert len(results) == 1
        assert results[0].data.decode("utf-8") == "hello reader"

    def test_decodes_barcode_when_not_qr_only(self, reader_tab):
        reader_tab.settings.scan_qr_only = False
        img = make_barcode_image("012345678905")
        results = reader_tab._decode_pil(img)
        assert len(results) == 1

    def test_qr_only_mode_ignores_barcodes(self, reader_tab):
        reader_tab.settings.scan_qr_only = True
        img = make_barcode_image("012345678905")
        results = reader_tab._decode_pil(img)
        assert results == []

    def test_qr_only_mode_still_finds_qr(self, reader_tab):
        reader_tab.settings.scan_qr_only = True
        img = make_qr_image("still works")
        results = reader_tab._decode_pil(img)
        assert len(results) == 1
        assert results[0].data.decode("utf-8") == "still works"

    def test_blank_image_returns_empty_list(self, reader_tab):
        img = Image.new("RGB", (200, 200), "white")
        results = reader_tab._decode_pil(img)
        assert results == []

    def test_decode_exception_is_caught(self, reader_tab, monkeypatch):
        def raise_err(*a, **k):
            raise RuntimeError("boom")
        monkeypatch.setattr("tab_reader.zbar_decode", raise_err)
        img = Image.new("RGB", (10, 10), "white")
        results = reader_tab._decode_pil(img)
        assert results == []


class TestDecodePath:
    def test_decode_path_updates_preview_and_emits_signal(self, reader_tab, tmp_path):
        path = tmp_path / "qr.png"
        make_qr_image("path decode test").save(path)

        received = {}
        reader_tab.decoded.connect(lambda t, d, s: received.update(type=t, data=d, source=s))

        reader_tab._decode_path(str(path))

        assert received["data"] == "path decode test"
        assert received["source"] == str(path)

    def test_decode_path_missing_file_shows_error(self, reader_tab, monkeypatch):
        called = {}
        monkeypatch.setattr("tab_reader.show_error", lambda parent, title, msg: called.setdefault("title", title))
        reader_tab._decode_path("/nonexistent/path/to/file.png")
        assert called.get("title") == "Decode Failed"
