"""
DICOM Viewer - Main Entry Point
================================
Launch the DICOM Viewer application.
"""

import logging
import sys
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="pydicom")  # noqa: E402

import warnings  # noqa: F811 - already imported, this suppresses the filter placement issue

from PyQt5.QtCore import Qt  # noqa: E402
from PyQt5.QtWidgets import QApplication  # noqa: E402

from app.gui.main_window import MainWindow  # noqa: E402
from app.utils.logger import setup_logger  # noqa: E402
from config.settings import APP_TITLE, APP_VERSION  # noqa: E402


def main():
    """Application entry point."""
    setup_logger()
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {APP_TITLE} v{APP_VERSION}")

    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setApplicationVersion(APP_VERSION)

    window = MainWindow()
    window.show()

    logger.info("Application started successfully.")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
