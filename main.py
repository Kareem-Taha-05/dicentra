"""
DICOM Viewer - Main Entry Point
================================
Launch the DICOM Viewer application.
"""

import sys
import logging
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydicom")
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from app.gui.main_window import MainWindow
from app.utils.logger import setup_logger
from config.settings import APP_TITLE, APP_VERSION


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
