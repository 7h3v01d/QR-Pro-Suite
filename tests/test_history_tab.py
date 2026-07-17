import time

import pytest
from PyQt6 import QtWidgets

from core import HistoryItem, HistoryModel
from tab_history import HistoryTab


def item(action, code_type, data):
    return HistoryItem(timestamp=time.time(), action=action, code_type=code_type, data=data, source="s", output="o")


@pytest.fixture
def history_tab(qapp):
    model = HistoryModel([
        item("generate", "QR", "alpha payload"),
        item("decode", "EAN13", "beta payload"),
        item("generate", "vCard", "gamma contact"),
    ])
    return HistoryTab(model)


class TestFiltering:
    def test_initial_state_shows_all(self, history_tab):
        assert history_tab.proxy.rowCount() == 3

    def test_filter_generate_only(self, history_tab):
        history_tab._set_filter("generate")
        assert history_tab.proxy.rowCount() == 2
        assert history_tab.filter_gen.isChecked() is True
        assert history_tab.filter_all.isChecked() is False

    def test_filter_decode_only(self, history_tab):
        history_tab._set_filter("decode")
        assert history_tab.proxy.rowCount() == 1

    def test_filter_all_resets(self, history_tab):
        history_tab._set_filter("decode")
        history_tab._set_filter("all")
        assert history_tab.proxy.rowCount() == 3
        assert history_tab.filter_all.isChecked() is True

    def test_search_narrows_results(self, history_tab):
        history_tab.search_edit.setText("beta")
        assert history_tab.proxy.rowCount() == 1

    def test_search_no_match_yields_zero_rows(self, history_tab):
        history_tab.search_edit.setText("nonexistent-string-xyz")
        assert history_tab.proxy.rowCount() == 0


class TestEntryCount:
    def test_updates_on_add(self, history_tab):
        history_tab.model.add(item("decode", "URL", "delta"))
        assert history_tab.entry_count.text() == "4 entries"

    def test_updates_on_clear(self, history_tab):
        history_tab.model.clear()
        assert history_tab.entry_count.text() == "0 entries"

    def test_shows_filtered_vs_total_counts(self, history_tab):
        # Note: _update_count is only wired to the model's modelReset/rowsInserted
        # signals, not to proxy filter changes, so it must be invoked explicitly
        # after changing the filter for the label to reflect the new counts.
        history_tab._set_filter("decode")
        history_tab._update_count()
        assert history_tab.entry_count.text() == "1 / 3 entries"


class TestExportAndClear:
    def test_export_writes_csv(self, history_tab, tmp_path, monkeypatch):
        out_path = tmp_path / "export.csv"
        monkeypatch.setattr(
            QtWidgets.QFileDialog, "getSaveFileName",
            staticmethod(lambda *a, **k: (str(out_path), "CSV (*.csv)"))
        )
        history_tab._export()
        assert out_path.exists()
        content = out_path.read_text()
        assert "alpha payload" in content

    def test_export_cancelled_dialog_does_nothing(self, history_tab, monkeypatch):
        monkeypatch.setattr(
            QtWidgets.QFileDialog, "getSaveFileName",
            staticmethod(lambda *a, **k: ("", ""))
        )
        # should not raise even though no path was chosen
        history_tab._export()

    def test_clear_confirmed_empties_model(self, history_tab, monkeypatch):
        # conftest's _suppress_modal_dialogs autouse fixture already makes
        # QMessageBox.question return Yes.
        history_tab._clear()
        assert history_tab.model.rowCount() == 0

    def test_clear_declined_keeps_items(self, history_tab, monkeypatch):
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "question",
            staticmethod(lambda *a, **k: QtWidgets.QMessageBox.StandardButton.Cancel)
        )
        history_tab._clear()
        assert history_tab.model.rowCount() == 3
