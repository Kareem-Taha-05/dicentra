"""
Application-wide configuration and constants.
"""

import os

# ── Application Identity ──────────────────────────────────────────────────────
APP_TITLE = "Dicentra"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Dicentra"

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")

os.makedirs(LOGS_DIR, exist_ok=True)

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_FILE = os.path.join(LOGS_DIR, "dicentra.log")
LOG_LEVEL = "DEBUG"  # DEBUG | INFO | WARNING | ERROR

# ── Image Viewer ──────────────────────────────────────────────────────────────
IMAGE_DISPLAY_SIZE = (600, 600)  # (width, height) pixels
M2D_FRAME_INTERVAL = 100  # milliseconds between frames

# ── 3-D Tile Viewer ───────────────────────────────────────────────────────────
TILE_WIDTH = 180
TILE_HEIGHT = 180
TILE_COLUMNS = 5
TILE_PADDING = 12

# ── Anonymisation ─────────────────────────────────────────────────────────────
ANONYMISED_GENDER = "O"

# ── Metadata table ────────────────────────────────────────────────────────────
METADATA_NAME_COL_WIDTH = 260

# ── Window / Level ────────────────────────────────────────────────────────────
WL_PRESETS = {
    # Standard radiological W/L presets (window_width, window_center)
    # W = range of HU values shown, C = HU value at midpoint (50% gray)
    "Brain": (80, 40),  # gray/white matter differentiation
    "Subdural": (200, 75),  # blood collections near brain surface
    "Stroke": (8, 32),  # subtle early ischaemia
    "Bone": (2000, 300),  # cortical bone and trabecular detail
    "Soft Tissue": (400, 50),  # general abdomen / organs
    "Lung": (1500, -600),  # airways and parenchyma
    "Liver": (150, 30),  # hepatic parenchyma
}
WL_DEFAULT_WIDTH = 400
WL_DEFAULT_CENTER = 40
# On load the viewer auto-computes W/L from the data range (shows full image)

# ── Series Browser ────────────────────────────────────────────────────────────
SERIES_THUMB_SIZE = 64  # px — thumbnail width/height in series panel
