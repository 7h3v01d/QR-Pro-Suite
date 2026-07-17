import os

import pytest
import qrcode
from PIL import Image

from tab_batch import BatchWorker


def run_worker(task, data):
    """Run a BatchWorker synchronously (call .run() directly instead of
    .start(), so we don't need a Qt event loop) and collect emitted results."""
    worker = BatchWorker(task, data)
    collected = {}
    worker.finished.connect(lambda items: collected.setdefault("items", items))
    worker.run()
    return collected["items"]


class TestBatchGenerate:
    def test_generates_qr_codes_from_rows(self, tmp_path):
        rows = [
            {"data": "https://example.com", "type": "QR Code", "filename": "one.png"},
            {"data": "hello world", "type": "QR Code", "filename": "two.png"},
        ]
        items = run_worker("generate", {"rows": rows, "out_dir": str(tmp_path)})

        assert len(items) == 2
        for item, row in zip(items, rows):
            assert item.action == "generate"
            assert item.data == row["data"]
            assert os.path.exists(item.output)
            assert Image.open(item.output).size[0] > 0

    def test_generates_barcode_from_rows(self, tmp_path):
        rows = [{"data": "012345678905", "type": "EAN-13", "filename": "ean.png"}]
        items = run_worker("generate", {"rows": rows, "out_dir": str(tmp_path)})
        assert len(items) == 1
        assert items[0].action == "generate"
        assert os.path.exists(items[0].output)

    def test_skips_rows_with_empty_data(self, tmp_path):
        rows = [
            {"data": "", "type": "QR Code", "filename": "skip.png"},
            {"data": "kept", "type": "QR Code", "filename": "keep.png"},
        ]
        items = run_worker("generate", {"rows": rows, "out_dir": str(tmp_path)})
        assert len(items) == 1
        assert items[0].data == "kept"

    def test_defaults_filename_when_missing(self, tmp_path):
        rows = [{"data": "no filename given", "type": "QR Code", "filename": ""}]
        items = run_worker("generate", {"rows": rows, "out_dir": str(tmp_path)})
        assert len(items) == 1
        assert os.path.basename(items[0].output) == "code_1.png"

    def test_defaults_type_when_missing(self, tmp_path):
        rows = [{"data": "typeless", "filename": "f.png"}]
        items = run_worker("generate", {"rows": rows, "out_dir": str(tmp_path)})
        assert len(items) == 1
        assert items[0].code_type == "QR Code"

    def test_bad_barcode_data_records_error_item(self, tmp_path):
        # EAN-13 requires a numeric string of a specific length; this should fail.
        rows = [{"data": "not-a-valid-ean", "type": "EAN-13", "filename": "bad.png"}]
        items = run_worker("generate", {"rows": rows, "out_dir": str(tmp_path)})
        assert len(items) == 1
        assert items[0].data.startswith("ERROR")

    def test_creates_output_subdirectories(self, tmp_path):
        out_dir = tmp_path / "nested" / "dir"
        rows = [{"data": "x", "type": "QR Code", "filename": "sub/inner.png"}]
        items = run_worker("generate", {"rows": rows, "out_dir": str(out_dir)})
        assert len(items) == 1
        assert os.path.exists(items[0].output)


class TestBatchDecode:
    def _make_qr_image(self, path, payload="batch decode test"):
        qr = qrcode.QRCode(border=2)
        qr.add_data(payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        img.save(path)
        return payload

    def test_decodes_valid_qr_images(self, tmp_path):
        path = tmp_path / "code.png"
        payload = self._make_qr_image(path)

        items = run_worker("decode", {"paths": [str(path)]})
        assert len(items) == 1
        assert items[0].action == "decode"
        assert items[0].data == payload
        assert items[0].source == str(path)

    def test_reports_no_code_found_for_blank_image(self, tmp_path):
        path = tmp_path / "blank.png"
        Image.new("RGB", (100, 100), "white").save(path)

        items = run_worker("decode", {"paths": [str(path)]})
        assert len(items) == 1
        assert items[0].data == "NO CODE FOUND"
        assert items[0].code_type == "N/A"

    def test_reports_error_for_unreadable_file(self, tmp_path):
        path = tmp_path / "not_an_image.png"
        path.write_text("this is not image data")

        items = run_worker("decode", {"paths": [str(path)]})
        assert len(items) == 1
        assert items[0].code_type == "ERROR"

    def test_decodes_multiple_images(self, tmp_path):
        p1, p2 = tmp_path / "a.png", tmp_path / "b.png"
        payload1 = self._make_qr_image(p1, "payload one")
        payload2 = self._make_qr_image(p2, "payload two")

        items = run_worker("decode", {"paths": [str(p1), str(p2)]})
        assert len(items) == 2
        datas = {it.data for it in items}
        assert datas == {payload1, payload2}

    def test_progress_signal_emitted_per_item(self, tmp_path):
        p1, p2 = tmp_path / "a.png", tmp_path / "b.png"
        self._make_qr_image(p1, "one")
        self._make_qr_image(p2, "two")

        worker = BatchWorker("decode", {"paths": [str(p1), str(p2)]})
        progress_calls = []
        worker.progress.connect(lambda cur, total, msg: progress_calls.append((cur, total)))
        worker.run()

        assert progress_calls == [(1, 2), (2, 2)]
