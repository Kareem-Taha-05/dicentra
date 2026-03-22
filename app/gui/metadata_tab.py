"""app/gui/metadata_tab.py — Metadata tab, Dicentra theme."""
from __future__ import annotations
from typing import List
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QFileDialog, QHBoxLayout, QHeaderView, QInputDialog,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget, QFrame,
)
from app.data.dicom_model import TagRow
from app.gui.widgets import make_button, make_separator

# Category chips: (label, emoji-hint, tooltip)
_CHIPS = [
    ("All Tags",    "≡",  "Every tag in the file"),
    ("Patient",     "👤", "Patient demographics — name, ID, DOB, sex, age, weight…"),
    ("Study",       "📋", "Study identifiers, dates, accession number, requesting physician…"),
    ("Modality",    "🔬", "Modality, series, acquisition parameters (kVP, TR, TE, slice thickness…)"),
    ("Equipment",   "🏥", "Manufacturer, station, institution, performing/reading physicians…"),
    ("Image",       "🖼", "Image type, UID, orientation, position, window/level, rescale…"),
    ("Pixel Data",  "⬛", "Rows, columns, bits, pixel spacing, pixel data…"),
]

_CHIP_SS = """
    QPushButton {{
        background: {bg};
        color: {fg};
        border: 1px solid {br};
        border-radius: 7px;
        padding: 0 14px;
        font-family: 'Outfit', sans-serif;
        font-size: 11px; font-weight: 500;
        min-height: 30px;
    }}
    QPushButton:hover {{
        background: rgba(124,58,237,0.20);
        color: #DDD6FE;
        border-color: rgba(124,58,237,0.50);
    }}
"""
_CHIP_INACTIVE = _CHIP_SS.format(
    bg="rgba(124,58,237,0.07)", fg="#C0BCDC", br="rgba(124,58,237,0.16)"
)
_CHIP_ACTIVE = _CHIP_SS.format(
    bg="rgba(124,58,237,0.28)", fg="#EDE9FE", br="rgba(124,58,237,0.65)"
)

# Tag colours per column
_TAG_COL   = QColor("#A78BFA")   # violet — tag address
_NAME_COL  = QColor("#C8C5E8")   # light lavender — name
_VALUE_COL = QColor("#F0EEFF")   # near-white — value (most important)


class MetadataTab(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._ctrl        = controller
        self._event_count = 0
        self._active_chip = 0
        self._chips: List[QPushButton] = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 14)
        root.setSpacing(10)

        # ── Category chips ─────────────────────────────────────────────────
        chips_row = QHBoxLayout(); chips_row.setSpacing(6)
        for i, (label, icon, tip) in enumerate(_CHIPS):
            btn = QPushButton(f"{icon}  {label}")
            btn.setEnabled(False)
            btn.setToolTip(tip)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(_CHIP_INACTIVE)
            btn.clicked.connect(lambda _, idx=i: self._on_chip(idx))
            self._chips.append(btn)
            chips_row.addWidget(btn)
        chips_row.addStretch()

        self._btn_anon = QPushButton("🔒  Anonymize")
        self._btn_anon.setEnabled(False)
        self._btn_anon.setFixedHeight(30)
        self._btn_anon.setCursor(Qt.PointingHandCursor)
        self._btn_anon.setStyleSheet("""
            QPushButton {
                background: rgba(255,107,107,0.10);
                color: #FCA5A5;
                border: 1px solid rgba(255,107,107,0.30);
                border-radius: 7px; padding: 0 14px;
                font-family: 'Outfit',sans-serif; font-size:11px; font-weight:500;
                min-height: 30px;
            }
            QPushButton:hover {
                background: rgba(255,107,107,0.20); color: #FFC9C9;
                border-color: rgba(255,107,107,0.55);
            }
            QPushButton:disabled { color: #3D1F1F; border-color: rgba(255,107,107,0.08); }
        """)
        chips_row.addWidget(self._btn_anon)
        root.addLayout(chips_row)

        # ── Search bar ─────────────────────────────────────────────────────
        sr = QHBoxLayout(); sr.setSpacing(8)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search tags by name or keyword…")
        self._btn_search = make_button("Search", "primary", min_width=90)
        sr.addWidget(self._search, stretch=1)
        sr.addWidget(self._btn_search)
        root.addLayout(sr)

        # ── Table ──────────────────────────────────────────────────────────
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["TAG", "NAME", "VALUE"])
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.Interactive)
        hdr.setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.setColumnWidth(0, 120)
        self._table.setColumnWidth(1, 260)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setShowGrid(False)
        self._table.setWordWrap(False)
        self._table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._table.verticalHeader().setDefaultSectionSize(28)  # compact rows

        # Custom row styling via stylesheet
        self._table.setStyleSheet("""
            QTableWidget {
                background: #07050F;
                border: 1px solid rgba(124,58,237,0.20);
                border-radius: 10px;
                gridline-color: transparent;
                selection-background-color: rgba(124,58,237,0.22);
                selection-color: #F0EEFF;
                alternate-background-color: rgba(124,58,237,0.05);
                font-family: 'JetBrains Mono', monospace;
                font-size: 12px;
                outline: 0;
            }
            QTableWidget::item {
                padding: 4px 12px;
                border: none;
                border-bottom: 1px solid rgba(124,58,237,0.06);
            }
            QTableWidget::item:selected { color: #F0EEFF; }
            QTableWidget::item:hover { background: rgba(124,58,237,0.10); }
            QHeaderView::section {
                background: #0E0B1A;
                color: #8884A8;
                padding: 8px 12px;
                border: none;
                border-bottom: 2px solid rgba(124,58,237,0.28);
                font-family: 'Outfit', sans-serif;
                font-size: 10px; font-weight: 700;
                letter-spacing: 1.8px; text-transform: uppercase;
            }
        """)
        root.addWidget(self._table, stretch=1)

        # ── Tag count status ───────────────────────────────────────────────
        count_row = QHBoxLayout(); count_row.setContentsMargins(4, 0, 4, 0)
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(
            "color:#8884A8; font-family:'JetBrains Mono',monospace; font-size:10px;"
        )
        count_row.addStretch()
        count_row.addWidget(self._count_lbl)
        root.addLayout(count_row)

        # ── Activity log ───────────────────────────────────────────────────
        log_hdr = QHBoxLayout()
        lbl = QLabel("Activity Log")
        lbl.setStyleSheet("color:#C0BCDC; font-family:'Outfit',sans-serif; font-size:11px; font-weight:600;")
        self._log_count = QLabel("0 events")
        self._log_count.setStyleSheet(
            "color:#8884A8; font-family:'JetBrains Mono',monospace; font-size:10px;"
        )
        log_hdr.addWidget(lbl); log_hdr.addStretch(); log_hdr.addWidget(self._log_count)
        root.addLayout(log_hdr)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(80)
        self._log.setStyleSheet("""
            QTextEdit {
                background: #07050F;
                border: 1px solid rgba(124,58,237,0.14);
                border-radius: 8px;
                padding: 8px 12px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                color: #C8C5E8;
            }
        """)
        root.addWidget(self._log)

    def _connect_signals(self):
        _actions = [
            self._ctrl.get_all_tags,
            self._ctrl.get_patient_info,
            self._ctrl.get_study_info,
            self._ctrl.get_modality_info,
            self._ctrl.get_physician_info,
            self._ctrl.get_image_info,
            self._ctrl.get_pixel_data_info,
        ]
        for i, action in enumerate(_actions):
            self._chips[i].clicked.connect(action)

        self._btn_anon.clicked.connect(self._on_anon)
        self._btn_search.clicked.connect(self._on_search)
        self._search.returnPressed.connect(self._on_search)
        self._ctrl.file_loaded.connect(self._on_loaded)
        self._ctrl.metadata_rows_ready.connect(self._populate)
        self._ctrl.status_message.connect(self._log_msg)

    def _on_chip(self, idx: int):
        # Highlight active chip
        for i, chip in enumerate(self._chips):
            chip.setStyleSheet(_CHIP_ACTIVE if i == idx else _CHIP_INACTIVE)
        self._active_chip = idx

    def _on_loaded(self, _):
        for c in self._chips: c.setEnabled(True)
        self._btn_anon.setEnabled(True)
        # Auto-load all tags
        self._chips[0].click()

    def _on_search(self):
        q = self._search.text().strip()
        # Clear active chip highlight when searching
        for c in self._chips: c.setStyleSheet(_CHIP_INACTIVE)
        if q: self._ctrl.search_tags(q)
        else: self._chips[0].click()

    def _on_anon(self):
        prefix, ok = QInputDialog.getText(self, "Anonymize DICOM", "Prefix for anonymized fields:")
        if not (ok and prefix): return
        path, _ = QFileDialog.getSaveFileName(self, "Save Anonymized File", "", "DICOM (*.dcm)")
        if path: self._ctrl.anonymize_and_save(prefix, path)

    def _populate(self, rows: List[TagRow]):
        self._table.setRowCount(0)
        self._table.setSortingEnabled(False)

        for row in rows:
            pos = self._table.rowCount()
            self._table.insertRow(pos)

            # TAG column — violet monospace
            t = QTableWidgetItem(row.tag)
            t.setForeground(_TAG_COL)
            t.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self._table.setItem(pos, 0, t)

            # NAME column — light lavender
            n = QTableWidgetItem(row.name)
            n.setForeground(_NAME_COL)
            self._table.setItem(pos, 1, n)

            # VALUE column — near-white (most readable)
            v = QTableWidgetItem(str(row.value)[:200])  # truncate very long values
            v.setForeground(_VALUE_COL)
            self._table.setItem(pos, 2, v)

        rc = self._table.rowCount()
        self._count_lbl.setText(f"{rc} tag{'s' if rc != 1 else ''}")
        if self._table.horizontalHeaderItem(0):
            self._table.horizontalHeaderItem(0).setText(f"TAG  ·  {rc}")

        self._table.setSortingEnabled(True)

    def _log_msg(self, msg: str):
        self._event_count += 1
        self._log_count.setText(f"{self._event_count} events")
        if any(w in msg.lower() for w in ("error","fail")):
            color = "#FCA5A5"
        elif any(w in msg.lower() for w in ("loaded","saved","success","displayed")):
            color = "#6EE7B7"
        else:
            color = "#C8C5E8"
        self._log.append(
            f'<span style="color:{color};font-family:\'JetBrains Mono\',monospace;'
            f'font-size:11px;">{msg}</span>'
        )
