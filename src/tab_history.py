"""
QR Professional Suite — History Tab
Full session history with search and export.
"""

import csv
import io
import time

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt

from core import HistoryModel, show_info
from widgets import SectionHeader, Divider, StatusChip


class HistoryTab(QtWidgets.QWidget):
    def __init__(self, model: HistoryModel):
        super().__init__()
        self.model = model
        self._build_ui()

    def _build_ui(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # Header row
        hdr = QtWidgets.QHBoxLayout()
        hdr.addWidget(SectionHeader("History", "All generate and decode actions this session"))
        hdr.addStretch(1)

        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Search history…")
        self.search_edit.setFixedWidth(220)
        self.search_edit.setClearButtonEnabled(True)
        hdr.addWidget(self.search_edit)
        root.addLayout(hdr)
        root.addWidget(Divider())

        # Filter row
        filter_row = QtWidgets.QHBoxLayout()
        filter_row.setSpacing(8)
        filter_lbl = QtWidgets.QLabel("FILTER")
        filter_lbl.setObjectName("sectionLabel")
        filter_row.addWidget(filter_lbl)

        self.filter_all = self._filter_btn("All", True)
        self.filter_gen = self._filter_btn("Generate", False)
        self.filter_dec = self._filter_btn("Decode", False)
        filter_row.addWidget(self.filter_all)
        filter_row.addWidget(self.filter_gen)
        filter_row.addWidget(self.filter_dec)
        filter_row.addStretch(1)

        self.entry_count = QtWidgets.QLabel("0 entries")
        self.entry_count.setStyleSheet("color: #4B5563; font-size: 11px;")
        filter_row.addWidget(self.entry_count)

        root.addLayout(filter_row)

        # Table
        self.proxy = QtCore.QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)

        self.table = QtWidgets.QTableView()
        self.table.setModel(self.proxy)
        self.table.setSelectionBehavior(QtWidgets.QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QtWidgets.QTableView.SelectionMode.ExtendedSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)

        # Column widths
        header = self.table.horizontalHeader()
        header.resizeSection(0, 150)  # time
        header.resizeSection(1, 80)   # action
        header.resizeSection(2, 100)  # type
        header.resizeSection(3, 280)  # data
        header.resizeSection(4, 180)  # source

        root.addWidget(self.table, 1)

        # Bottom actions
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(8)
        self.status_chip = StatusChip()
        btn_row.addWidget(self.status_chip)
        btn_row.addStretch(1)
        self.copy_btn = QtWidgets.QPushButton("Copy Selected")
        self.export_btn = QtWidgets.QPushButton("Export CSV…")
        self.export_btn.setObjectName("primaryBtn")
        self.clear_btn = QtWidgets.QPushButton("Clear History")
        self.clear_btn.setObjectName("dangerBtn")
        btn_row.addWidget(self.copy_btn)
        btn_row.addWidget(self.export_btn)
        btn_row.addWidget(self.clear_btn)
        root.addLayout(btn_row)

        # Connections
        self.search_edit.textChanged.connect(self.proxy.setFilterFixedString)
        self.filter_all.clicked.connect(lambda: self._set_filter("all"))
        self.filter_gen.clicked.connect(lambda: self._set_filter("generate"))
        self.filter_dec.clicked.connect(lambda: self._set_filter("decode"))
        self.export_btn.clicked.connect(self._export)
        self.copy_btn.clicked.connect(self._copy_selected)
        self.clear_btn.clicked.connect(self._clear)
        self.model.modelReset.connect(self._update_count)
        self.model.rowsInserted.connect(self._update_count)

    def _filter_btn(self, label: str, active: bool) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton(label)
        btn.setCheckable(True)
        btn.setChecked(active)
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #1E2130;
                border-radius: 4px;
                padding: 4px 12px;
                color: #6B7280;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:checked {
                background: rgba(37, 99, 235, 0.15);
                border-color: #2563EB;
                color: #60A5FA;
            }
            QPushButton:hover { color: #C0C8D8; }
        """)
        return btn

    def _set_filter(self, kind: str):
        self.filter_all.setChecked(kind == "all")
        self.filter_gen.setChecked(kind == "generate")
        self.filter_dec.setChecked(kind == "decode")
        if kind == "all":
            self.proxy.setFilterKeyColumn(-1)
            self.proxy.setFilterFixedString(self.search_edit.text())
        else:
            self.proxy.setFilterKeyColumn(1)
            self.proxy.setFilterFixedString(kind.upper())

    def _update_count(self):
        count = self.proxy.rowCount()
        total = self.model.rowCount()
        if count == total:
            self.entry_count.setText(f"{total} entries")
        else:
            self.entry_count.setText(f"{count} / {total} entries")

    def _export(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export History", "qr_history.csv", filter="CSV (*.csv)"
        )
        if path:
            self.model.export_csv(path)
            self.status_chip.set(f"Exported to {path.split('/')[-1]}", "success")

    def _copy_selected(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(self.model.HEADERS)
        for proxy_idx in selected:
            src_idx = self.proxy.mapToSource(proxy_idx)
            it = self.model.items[src_idx.row()]
            w.writerow([
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(it.timestamp)),
                it.action, it.code_type, it.data, it.source, it.output
            ])
        QtWidgets.QApplication.clipboard().setText(buf.getvalue())
        self.status_chip.set(f"Copied {len(selected)} row(s)", "success")

    def _clear(self):
        reply = QtWidgets.QMessageBox.question(
            self, "Clear History",
            "Clear all history entries for this session?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.Cancel
        )
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.model.clear()
            self.status_chip.set("History cleared", "neutral")
