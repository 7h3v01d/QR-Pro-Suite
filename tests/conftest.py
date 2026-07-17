"""
Shared pytest fixtures for the QR Professional Suite test suite.

The application modules (core, widgets, tab_*, main) use flat imports
(e.g. `from core import ...`) rather than package-relative imports, since
they are designed to be run with `src/` as the working directory /
on sys.path (see README: "cd src && python main.py"). We replicate that
here by inserting `src/` at the front of sys.path.

All GUI tests run against the Qt "offscreen" platform plugin so the
suite can run headlessly (no X server / display required).
"""
import os
import sys
from pathlib import Path

# Must be set before PyQt6 is imported anywhere.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pytest
from PyQt6 import QtWidgets


@pytest.fixture(scope="session")
def qapp():
    """A single QApplication instance shared across the whole test session."""
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(["test"])
    yield app


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path, monkeypatch):
    """
    Run every test from a fresh temp directory so that AppSettings.save()/load()
    (which writes "qr_pro_settings.json" to the CWD) never touches the real
    project files, and so batch/history CSV exports land somewhere disposable.
    """
    monkeypatch.chdir(tmp_path)
    yield tmp_path


@pytest.fixture(autouse=True)
def _suppress_modal_dialogs(monkeypatch):
    """
    Several widgets pop up blocking QMessageBox dialogs (show_info/show_error,
    and direct QMessageBox.question/exec calls) on user actions. Those would
    hang a headless test run waiting for a click that will never come, so we
    neutralize them by default. Individual tests can still assert these were
    called by wrapping/inspecting, or override this fixture's patches locally.
    """
    monkeypatch.setattr(QtWidgets.QMessageBox, "exec", lambda self: None)
    monkeypatch.setattr(
        QtWidgets.QMessageBox, "question",
        staticmethod(lambda *a, **k: QtWidgets.QMessageBox.StandardButton.Yes)
    )
    yield
