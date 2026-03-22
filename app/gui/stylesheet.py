"""
app/gui/stylesheet.py
=====================
Dicentra — "Deep Space Medical" theme.

Text colour hierarchy (readability-first):
  Primary text:    #F0EEFF  — near-white with just a trace of violet warmth
  Secondary text:  #C8C5E8  — light lavender-white, clearly readable
  Tertiary text:   #8884A8  — muted violet-grey, supporting / hints
  Disabled text:   #3D3860  — barely visible, truly inactive only

Background levels:
  Base:    #0E0B1A  — deep indigo-black
  Surface: #151225  — elevated panel
  Card:    #1C1830  — card / input background
  Header:  #07050F  — darkest surface (header + status bar)
"""

THEME = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600&family=JetBrains+Mono:wght@300;400;500&display=swap');

/* ── Base ──────────────────────────────────────────────────────────────── */
QMainWindow, QWidget, QDialog {
    background-color: #0E0B1A;
    color: #F0EEFF;
    font-family: 'Outfit', 'Segoe UI', sans-serif;
    font-size: 13px;
    font-weight: 400;
}

/* ── Tab Widget ────────────────────────────────────────────────────────── */
QTabWidget::pane {
    background: #0E0B1A;
    border: none;
    border-top: 1px solid rgba(124,58,237,0.22);
}
QTabBar {
    background: #07050F;
    border-bottom: 1px solid rgba(124,58,237,0.18);
}
QTabBar::tab {
    background: transparent;
    color: #8884A8;
    padding: 12px 28px 11px;
    border: none;
    border-bottom: 2px solid transparent;
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    min-width: 120px;
}
QTabBar::tab:selected {
    color: #DDD6FE;
    border-bottom: 2px solid #7C3AED;
    background: rgba(124,58,237,0.08);
}
QTabBar::tab:hover:!selected {
    color: #C4B5FD;
    background: rgba(255,255,255,0.03);
}

/* ── Push Buttons ──────────────────────────────────────────────────────── */
QPushButton {
    background: rgba(255,255,255,0.06);
    color: #D8D5F5;
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 8px;
    padding: 8px 18px;
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.2px;
    min-height: 34px;
}
QPushButton:hover {
    background: rgba(255,255,255,0.11);
    color: #F0EEFF;
    border-color: rgba(255,255,255,0.26);
}
QPushButton:pressed { background: rgba(255,255,255,0.03); }
QPushButton:disabled {
    background: transparent;
    color: #3D3860;
    border-color: rgba(255,255,255,0.05);
}

/* Violet primary */
QPushButton#primary {
    background: rgba(124,58,237,0.20);
    color: #DDD6FE;
    border: 1px solid rgba(124,58,237,0.45);
}
QPushButton#primary:hover {
    background: rgba(124,58,237,0.32);
    color: #EDE9FE;
    border-color: rgba(124,58,237,0.72);
}
QPushButton#primary:pressed { background: rgba(124,58,237,0.12); }
QPushButton#primary:disabled {
    color: #2D1F4A;
    border-color: rgba(124,58,237,0.08);
    background: transparent;
}

/* Coral / stop */
QPushButton#danger, QPushButton#amber {
    background: rgba(255,107,107,0.12);
    color: #FFC9C9;
    border: 1px solid rgba(255,107,107,0.34);
}
QPushButton#danger:hover, QPushButton#amber:hover {
    background: rgba(255,107,107,0.22);
    color: #FFE4E4;
    border-color: rgba(255,107,107,0.58);
}
QPushButton#danger:disabled, QPushButton#amber:disabled {
    color: #3D1F1F;
    border-color: rgba(255,107,107,0.06);
    background: transparent;
}

/* ── Labels ────────────────────────────────────────────────────────────── */
QLabel { color: #D8D5F5; background: transparent; }
QLabel#section_header {
    font-size: 10px; font-weight: 600; letter-spacing: 1.8px;
    color: #8884A8; text-transform: uppercase; padding-bottom: 4px;
}
QLabel#status_ok   { color: #6EE7B7; font-family: 'JetBrains Mono',monospace; font-size: 11px; }
QLabel#status_warn { color: #FDE68A; font-family: 'JetBrains Mono',monospace; font-size: 11px; }
QLabel#status_err  { color: #FFC9C9; font-family: 'JetBrains Mono',monospace; font-size: 11px; }
QLabel#mono        { font-family: 'JetBrains Mono',monospace; font-size: 12px; color: #D8D5F5; }
QLabel#image_canvas {
    background: #07050F;
    border: 1px solid rgba(124,58,237,0.14);
    border-radius: 12px;
}
QLabel#frame_badge {
    background: rgba(124,58,237,0.20);
    color: #DDD6FE;
    border: 1px solid rgba(124,58,237,0.44);
    border-radius: 6px;
    padding: 3px 10px;
    font-family: 'JetBrains Mono',monospace;
    font-size: 11px;
    font-weight: 500;
}

/* ── Line Edit ─────────────────────────────────────────────────────────── */
QLineEdit {
    background: #1C1830;
    color: #F0EEFF;
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 8px;
    padding: 8px 14px;
    font-family: 'JetBrains Mono',monospace;
    font-size: 12px;
    selection-background-color: rgba(124,58,237,0.38);
    min-height: 34px;
}
QLineEdit:focus {
    border-color: rgba(124,58,237,0.62);
    background: rgba(124,58,237,0.08);
    color: #F0EEFF;
}

/* ── Text Edit ─────────────────────────────────────────────────────────── */
QTextEdit, QPlainTextEdit {
    background: #07050F;
    color: #C8C5E8;
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 8px;
    padding: 10px 14px;
    font-family: 'JetBrains Mono',monospace;
    font-size: 11px;
    selection-background-color: rgba(124,58,237,0.30);
}

/* ── Table ─────────────────────────────────────────────────────────────── */
QTableWidget {
    background: #07050F;
    gridline-color: rgba(255,255,255,0.06);
    border: 1px solid rgba(124,58,237,0.16);
    border-radius: 10px;
    selection-background-color: rgba(124,58,237,0.20);
    selection-color: #F0EEFF;
    alternate-background-color: rgba(124,58,237,0.04);
    outline: 0;
    font-family: 'JetBrains Mono',monospace;
    font-size: 12px;
}
QTableWidget::item { padding: 8px 14px; border: none; color: #C8C5E8; }
QTableWidget::item:selected { color: #F0EEFF; }
QTableWidget::item:hover { background: rgba(124,58,237,0.09); }
QHeaderView { background: transparent; }
QHeaderView::section {
    background: #0E0B1A;
    color: #8884A8;
    padding: 9px 14px;
    border: none;
    border-bottom: 1px solid rgba(124,58,237,0.16);
    font-family: 'Outfit', sans-serif;
    font-size: 10px; font-weight: 600; letter-spacing: 1.4px;
    text-transform: uppercase;
}

/* ── Scrollbars ────────────────────────────────────────────────────────── */
QScrollBar:vertical   { background: transparent; width: 6px; margin: 0; }
QScrollBar:horizontal { background: transparent; height: 6px; margin: 0; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: rgba(124,58,237,0.32); border-radius: 3px; min-height: 24px; min-width: 24px;
}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background: rgba(124,58,237,0.52);
}
QScrollBar::add-line:vertical,  QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,  QScrollBar::sub-page:vertical,
QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal,QScrollBar::sub-page:horizontal {
    background: none; height: 0; width: 0;
}

/* ── Graphics View ─────────────────────────────────────────────────────── */
QGraphicsView {
    background: #07050F;
    border: 1px solid rgba(124,58,237,0.16);
    border-radius: 10px;
}

/* ── Status Bar ────────────────────────────────────────────────────────── */
QStatusBar {
    background: #07050F;
    color: #A8A5C8;
    font-family: 'JetBrains Mono',monospace;
    font-size: 11px;
    border-top: 1px solid rgba(124,58,237,0.14);
    padding: 3px 16px;
    min-height: 28px;
}
QStatusBar::item { border: none; }

/* ── Splitter ──────────────────────────────────────────────────────────── */
QSplitter::handle { background: rgba(124,58,237,0.12); width: 1px; height: 1px; }

/* ── Named containers ──────────────────────────────────────────────────── */
QWidget#header_bar    { background: #07050F; border-bottom: 1px solid rgba(124,58,237,0.18); }
QWidget#sidebar_panel { background: #0A0815; border-right:  1px solid rgba(124,58,237,0.14); }
QWidget#control_card {
    background: #151225;
    border: 1px solid rgba(124,58,237,0.18);
    border-radius: 12px;
}

/* ── Separators ────────────────────────────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    background: rgba(124,58,237,0.14); border: none;
    max-height: 1px; min-height: 1px; max-width: 1px; min-width: 1px;
}

/* ── Tooltip ───────────────────────────────────────────────────────────── */
QToolTip {
    background: #1C1830; color: #DDD6FE;
    border: 1px solid rgba(124,58,237,0.38);
    border-radius: 6px; padding: 6px 10px; font-size: 11px;
}

/* ── Input Dialog ──────────────────────────────────────────────────────── */
QInputDialog { background: #0E0B1A; }
QInputDialog QLabel { color: #F0EEFF; font-size: 13px; }
QInputDialog QLineEdit {
    background: #1C1830; color: #F0EEFF;
    border: 1px solid rgba(124,58,237,0.38);
    border-radius: 8px; padding: 8px 14px;
    font-family: 'JetBrains Mono',monospace;
}
"""
