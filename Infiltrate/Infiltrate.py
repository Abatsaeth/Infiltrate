#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Infiltrate - A minimalistic, modern, and fast image conversion tool.
This module serves as the application launcher and ensures a single instance.
"""

import os
import sys
import tempfile
import socket
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFontDatabase
from Scripts.main import MainWindow


def ensure_single_instance():
    """Ensures only one instance of the application is running."""
    # Use a socket as a lock mechanism
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Try to bind to a port that only one instance should use
        sock.bind(('localhost', 49152))  # Using a high port number
        return True  # This is the only instance
    except socket.error:
        return False  # Another instance is already running


def load_fonts():
    """Load custom fonts from the Content/Fonts directory."""
    fonts_dir = Path(__file__).parent / "Content" / "Fonts"
    
    # Load Century Gothic fonts
    QFontDatabase.addApplicationFont(str(fonts_dir / "centurygothic.ttf"))
    QFontDatabase.addApplicationFont(str(fonts_dir / "centurygothic_bold.ttf"))


def load_stylesheet():
    """Load the global stylesheet for the application."""
    # Dark theme with red accents
    return """
    /* Global Styles */
    QWidget {
        background-color: #121212;
        color: #FFFFFF;
        font-family: 'Century Gothic';
        font-size: 10pt;
    }
    
    /* Button Styles */
    QPushButton {
        background-color: #1E1E1E;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        color: #FFFFFF;
    }
    
    QPushButton:hover {
        background-color: #2A2A2A;
    }
    
    QPushButton:pressed {
        background-color: #E53935;  /* Red accent */
    }
    
    /* Tab Widget Styles */
    QTabWidget::pane {
        border: 1px solid #323232;
        background-color: #1E1E1E;
    }
    
    QTabBar::tab {
        background-color: #1E1E1E;
        color: #B0B0B0;
        padding: 8px 16px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    
    QTabBar::tab:selected {
        background-color: #2A2A2A;
        color: #FFFFFF;
    }
    
    QTabBar::tab:hover:!selected {
        background-color: #323232;
    }
    
    /* Label Styles */
    QLabel {
        color: #FFFFFF;
    }
    
    /* Progress Bar */
    QProgressBar {
        border: 1px solid #323232;
        border-radius: 2px;
        text-align: center;
        background-color: #1E1E1E;
    }
    
    QProgressBar::chunk {
        background-color: #E53935;  /* Red accent */
    }
    
    /* Scroll Area */
    QScrollArea {
        border: none;
    }
    
    /* Dropdown (ComboBox) */
    QComboBox {
        border: 1px solid #323232;
        border-radius: 4px;
        padding: 4px;
        background-color: #1E1E1E;
    }
    
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 15px;
        border-left-width: 1px;
        border-left-color: #323232;
        border-left-style: solid;
    }
    
    /* Table View */
    QTableView {
        gridline-color: #323232;
        background-color: #1E1E1E;
        alternate-background-color: #2A2A2A;
    }
    
    QHeaderView::section {
        background-color: #323232;
        padding: 4px;
        border: none;
        color: #FFFFFF;
    }
    
    /* Text Edit and Line Edit */
    QTextEdit, QLineEdit {
        border: 1px solid #323232;
        border-radius: 4px;
        padding: 4px;
        background-color: #1E1E1E;
    }
    
    /* Accent colors for specific elements */
    #logoLabel, #updateButton {
        color: #E53935;  /* Red accent */
    }
    """


def main():
    """Main entry point for the application."""
    # Check if another instance is already running
    if not ensure_single_instance():
        print("Infiltrate is already running.")
        sys.exit(1)
        
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Infiltrate")
    app.setApplicationVersion("1.0.0")
    
    # Load fonts and stylesheet
    load_fonts()
    app.setStyleSheet(load_stylesheet())
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Execute application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
