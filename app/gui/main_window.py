"""app/gui/main_window.py — wires sidebar info panels + frame nav."""
from __future__ import annotations
import logging
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QStatusBar, QTabWidget, QVBoxLayout, QWidget,
)
from app.gui.image_tab      import ImageTab
from app.gui.metadata_tab   import MetadataTab
from app.gui.series_browser import SeriesBrowser
from app.gui.stylesheet     import THEME
from app.gui.threed_tab     import TileViewerTab
from app.logic.controller   import DicomControllerExtended
from config.settings        import APP_TITLE, APP_VERSION

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._ctrl = DicomControllerExtended(self)
        self._browser_visible = True
        self._setup_window()
        self._build_ui()
        self.setStyleSheet(THEME)
        self._ctrl.status_message.connect(self._on_status)
        self._ctrl.file_loaded.connect(self._on_file_loaded)
        self._ctrl.series_loaded.connect(self._series_browser.populate)

        # Wire ruler measurements: ImageTab → SeriesBrowser sidebar card
        def _on_meas_added(label: str):
            self._series_browser.add_measurement(label)

        def _on_meas_cleared():
            self._series_browser.clear_measurements()

        self._img_tab.on_measurement_added    = _on_meas_added
        self._img_tab.on_measurements_cleared = _on_meas_cleared
        # Register the canvas-clear callback with the sidebar
        self._series_browser.set_clear_canvas_callback(self._img_tab.clear_measurements)

    def _setup_window(self):
        self.setWindowTitle(f"{APP_TITLE}  v{APP_VERSION}")
        self.setMinimumSize(1160, 740)
        self.resize(1440, 880)

    def _build_ui(self):
        central = QWidget()
        layout  = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setCentralWidget(central)

        # ── Header ─────────────────────────────────────────────────────────
        header = QWidget(); header.setObjectName("header_bar"); header.setFixedHeight(50)
        h = QHBoxLayout(header); h.setContentsMargins(16, 0, 20, 0); h.setSpacing(0)

        self._toggle = QPushButton("≡")
        self._toggle.setFixedSize(36, 36)
        self._toggle.setCursor(Qt.PointingHandCursor)
        self._toggle.setToolTip("Toggle sidebar  (Ctrl+B)")
        self._toggle.setStyleSheet("""
            QPushButton {
                background:rgba(124,58,237,0.10);color:#5A5080;
                border:1px solid rgba(124,58,237,0.20);border-radius:8px;
                font-size:16px;font-weight:400;
            }
            QPushButton:hover {background:rgba(124,58,237,0.22);color:#A78BFA;
                               border-color:rgba(124,58,237,0.50);}
        """)
        self._toggle.clicked.connect(self._toggle_browser)

        logo = QLabel("⬡")
        logo.setStyleSheet("color:#7C3AED;font-size:16px;margin:0 10px 0 14px;")
        name = QLabel(APP_TITLE.upper())
        name.setStyleSheet(
            "color:#5A5080;font-family:'Outfit','Segoe UI',sans-serif;"
            "font-size:12px;font-weight:600;letter-spacing:2.5px;"
        )
        ver = QLabel(f"  v{APP_VERSION}")
        ver.setStyleSheet(
            "color:#2D2A45;font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:0.5px;"
        )
        dot_sep = QLabel("  ·  ")
        dot_sep.setStyleSheet("color:#2D2A45;font-size:12px;")
        self._file_lbl = QLabel("no file loaded")
        self._file_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._file_lbl.setStyleSheet(
            "color:#2D2A45;font-family:'JetBrains Mono',monospace;font-size:10px;"
        )
        h.addWidget(self._toggle); h.addWidget(logo)
        h.addWidget(name); h.addWidget(ver); h.addWidget(dot_sep)
        h.addStretch(); h.addWidget(self._file_lbl)
        layout.addWidget(header)

        # ── Body ───────────────────────────────────────────────────────────
        body_w = QWidget()
        body   = QHBoxLayout(body_w); body.setSpacing(0); body.setContentsMargins(0,0,0,0)

        self._series_browser = SeriesBrowser()
        self._series_browser.series_selected.connect(self._on_series_event)
        self._series_browser.file_reopen_requested.connect(self._ctrl.load_file)
        body.addWidget(self._series_browser)

        vdiv = QFrame(); vdiv.setFrameShape(QFrame.VLine)
        vdiv.setStyleSheet(
            "background:rgba(124,58,237,0.12);border:none;max-width:1px;min-width:1px;"
        )
        body.addWidget(vdiv)

        self._tabs = QTabWidget(); self._tabs.setDocumentMode(True)
        self._img_tab  = ImageTab(self._ctrl)
        self._meta_tab = MetadataTab(self._ctrl)
        self._tile_tab = TileViewerTab(self._ctrl)
        self._tabs.addTab(self._img_tab,  "  Image Viewer  ")
        self._tabs.addTab(self._meta_tab, "  Metadata  ")
        self._tabs.addTab(self._tile_tab, "  3D · Tiles  ")
        body.addWidget(self._tabs, stretch=1)

        layout.addWidget(body_w, stretch=1)

        self._sb = QStatusBar(); self.setStatusBar(self._sb)
        self._sb.showMessage("Ready  ·  Open a DICOM file or folder to begin")

    def _toggle_browser(self):
        self._browser_visible = not self._browser_visible
        self._series_browser.setVisible(self._browser_visible)

    def _on_series_event(self, payload):
        if isinstance(payload, str):
            self._ctrl.load_series_folder(payload)
        elif isinstance(payload, list):
            self._ctrl.load_series_by_paths(payload)
            self._tabs.setCurrentIndex(0)

    def _on_status(self, msg: str):
        self._sb.showMessage(msg)

    def _on_file_loaded(self, path: str):
        short = path.replace("\\", "/").split("/")[-1]
        self._file_lbl.setText(short)
        self._file_lbl.setStyleSheet(
            "color:#5A3E90;font-family:'JetBrains Mono',monospace;font-size:10px;"
        )
        self.setWindowTitle(f"{APP_TITLE}  —  {short}")

        # Update sidebar cards
        self._series_browser.update_recent(path)
        try:
            ds = self._ctrl._model.dataset
            if ds:
                self._series_browser.update_file_info(path, ds)
        except Exception:
            pass
