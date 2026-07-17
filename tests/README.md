# QR Professional Suite — Test Suite

## Setup

```bash
pip install -r requirements-dev.txt
```

`pyzbar` also needs the system `zbar` shared library (`libzbar0` on
Debian/Ubuntu, `zbar` via Homebrew on macOS).

## Running

From the project root (the folder containing `src/` and `tests/`):

```bash
pytest
```

The suite runs headlessly against Qt's `offscreen` platform plugin (set
automatically in `tests/conftest.py`), so no display/X server is required.
Each test runs in its own temp working directory, so `AppSettings` reads/writes
and CSV exports never touch your real project files.

## What's covered

| File | Covers |
|---|---|
| `test_core.py` | `AppSettings` save/load, `HistoryModel`, `pil_to_qpixmap` |
| `test_generator_payloads.py` | Every Generator payload format (Text/URL, Wi-Fi, vCard, E-mail, SMS, Phone, Geo, Bitcoin, 1D barcodes) incl. validation errors |
| `test_generator_images.py` | Error-correction mapping, solid/gradient QR rendering, barcode rendering, logo embedding |
| `test_batch_worker.py` | `BatchWorker` CSV-driven generation and folder decoding, including error rows |
| `test_reader.py` | `ReaderTab` decode logic, QR-only mode, error handling |
| `test_widgets.py` | `ColorSwatch`, `StatusChip`, `DropZone`, `PreviewPanel`, and misc layout widgets |
| `test_history_tab.py` | Search/filter proxy model, entry count, export, clear |
| `test_settings_tab.py` | Save/reset round-tripping into `AppSettings` |

Not covered (would need a live camera/display and add little value under a
headless suite): the OpenCV camera feed in `tab_reader.ReaderTab._read_frame`,
and pixel-perfect UI styling.
