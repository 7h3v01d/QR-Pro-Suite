import pytest

from core import AppSettings
from tab_settings import SettingsTab


@pytest.fixture
def settings_tab(qapp):
    return SettingsTab(AppSettings())


class TestSave:
    def test_save_copies_widget_values_into_settings(self, settings_tab, tmp_path):
        settings_tab.camera_spin.setValue(4)
        settings_tab.qr_only_chk.setChecked(True)
        settings_tab.size_spin.setValue(20)
        settings_tab.border_spin.setValue(6)
        settings_tab.ec_combo.setCurrentText("Q (25%)")
        settings_tab.ontop_chk.setChecked(True)

        settings_tab._save()

        s = settings_tab.settings
        assert s.camera_index == 4
        assert s.scan_qr_only is True
        assert s.default_size == 20
        assert s.default_border == 6
        assert s.default_error_correction == "Q"
        assert s.always_on_top is True

    def test_save_persists_to_disk(self, settings_tab, tmp_path):
        settings_tab.camera_spin.setValue(7)
        settings_tab._save()
        saved_file = tmp_path / AppSettings.SETTINGS_FILE
        assert saved_file.exists()

    def test_save_emits_settings_changed(self, settings_tab):
        received = []
        settings_tab.settings_changed.connect(lambda: received.append(True))
        settings_tab._save()
        assert received == [True]


class TestReset:
    def test_reset_confirmed_restores_widget_defaults(self, settings_tab):
        settings_tab.camera_spin.setValue(9)
        settings_tab.qr_only_chk.setChecked(True)
        settings_tab.size_spin.setValue(30)
        settings_tab.border_spin.setValue(12)
        settings_tab.ontop_chk.setChecked(True)

        settings_tab._reset()  # autouse fixture makes QMessageBox.question -> Yes

        defaults = AppSettings()
        assert settings_tab.camera_spin.value() == defaults.camera_index
        assert settings_tab.qr_only_chk.isChecked() == defaults.scan_qr_only
        assert settings_tab.size_spin.value() == defaults.default_size
        assert settings_tab.border_spin.value() == defaults.default_border
        assert settings_tab.ontop_chk.isChecked() == defaults.always_on_top
        assert settings_tab.ec_combo.currentIndex() == 3

    def test_reset_declined_leaves_widgets_untouched(self, settings_tab, monkeypatch):
        from PyQt6 import QtWidgets
        monkeypatch.setattr(
            QtWidgets.QMessageBox, "question",
            staticmethod(lambda *a, **k: QtWidgets.QMessageBox.StandardButton.Cancel)
        )
        settings_tab.camera_spin.setValue(9)
        settings_tab._reset()
        assert settings_tab.camera_spin.value() == 9

    def test_reset_does_not_touch_underlying_settings_object(self, settings_tab):
        # _reset only updates widget state; it should not call settings.save()
        # or mutate settings until the user explicitly hits Save afterwards.
        settings_tab.settings.camera_index = 8
        settings_tab.camera_spin.setValue(9)
        settings_tab._reset()
        assert settings_tab.settings.camera_index == 8
