# QR Professional Suite v2.0

A comprehensive, production-quality QR code and barcode management application built with PyQt6.

---

<img width="1920" height="1040" alt="screenshot" src="https://github.com/user-attachments/assets/39a74b2b-5ac1-414e-9158-5f5210f1a121" />

---

## Features

### Generator Tab
- **8 QR formats**: Text/URL, Wi-Fi, vCard, E-mail, SMS, Phone, Geo Location, Bitcoin
- **4 barcode types**: EAN-13, Code 128, Code 39, UPC-A
- **Gradient styles**: Solid, Vertical, Horizontal, Radial, Diagonal
- **Full color control**: Custom foreground and background
- **Logo embedding** with white backing
- **Error correction control**: L / M / Q / H
- **Module size and border** configuration
- Copy to clipboard or save as PNG / JPEG / BMP

### Reader Tab
- Open image files (PNG, JPG, GIF, BMP, TIFF, WebP)
- **Drag-and-drop** decode
- **Live camera** decode with real-time feed
- Decode multiple codes from one image
- Per-result copy + URL launcher
- QR-only mode for improved camera stability

### Batch Tab
- **Batch generate** from a CSV file (data, type, filename columns)
- **Batch decode** an entire folder of images
- Recursive subfolder scanning
- Background worker thread (non-blocking UI)
- Progress bar + results log
- Auto-export results to CSV

### History Tab
- All session actions logged in real-time
- Search across all columns
- Filter by Generate / Decode
- Sortable columns
- Export to CSV
- Copy selected rows

### Settings Tab
- Camera index selection
- Default generation parameters
- Always-on-top window option
- Persistent settings via JSON

## Installation

```bash
pip install PyQt6 "qrcode[pil]" Pillow pyzbar opencv-python python-barcode
```

## Run

```bash
cd src
python main.py
```

## File Structure

```
src/
  main.py           — Entry point and main window
  core.py           — Data models, settings, utilities
  stylesheet.py     — Complete dark UI theme
  widgets.py        — Reusable custom widgets
  tab_generate.py   — Generator tab
  tab_reader.py     — Reader/decoder tab
  tab_batch.py      — Batch operations tab
  tab_history.py    — Session history tab
  tab_settings.py   — Settings tab
```
