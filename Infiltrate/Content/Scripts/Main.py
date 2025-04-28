#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main window module for Infiltrate application.
Implements the UI and core functionality.
"""

import os
import sys
import time
import platform
import pkg_resources
from enum import Enum
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox, QApplication, QMenu, QAction, QSizePolicy, QScrollArea,
    QCheckBox, QComboBox, QSpacerItem, QFrame, QLineEdit
)
from PyQt5.QtCore import (
    Qt, QSize, QPoint, QPropertyAnimation, QEasingCurve, QRect,
    QTimer, QEvent, QThread, pyqtSignal, QObject, QMimeData
)
from PyQt5.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QFont, QFontMetrics, 
    QDrag, QMouseEvent, QDragEnterEvent, QDropEvent, QResizeEvent,
    QPalette, QCursor, QCloseEvent
)

# Import application modules
from Scripts.ImageConverter import show_conversion_dialog
from Scripts.Updater import check_for_updates


class DependencyInfo:
    """Information about a dependency."""
    
    def __init__(self, name: str, installed_version: str = "", latest_version: str = ""):
        self.name = name
        self.installed_version = installed_version
        self.latest_version = latest_version
    
    @property
    def update_needed(self) -> bool:
        """Check if update is needed based on version strings."""
        if not self.installed_version or not self.latest_version:
            return False
        
        # Simple version comparison (this could be more sophisticated)
        return self.installed_version != self.latest_version


class CustomTitleBar(QWidget):
    """Custom title bar with minimize and close buttons."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QWidget {
                background-color: #0F0F0F;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QPushButton {
                background-color: transparent;
                border: none;
                color: #B0B0B0;
                font-size: 16px;
                padding: 5px;
            }
            
            QPushButton:hover {
                background-color: #2A2A2A;
                color: #FFFFFF;
            }
            
            QPushButton#close_button:hover {
                background-color: #E53935;
                color: #FFFFFF;
            }
        """)
        
        # Initialize UI
        self.init_ui()
        
        # For window dragging
        self.dragging = False
        self.drag_position = QPoint()
    
    def init_ui(self):
        """Set up the title bar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        
        # Application title
        title_label = QLabel("Infiltrate")
        title_label.setStyleSheet("color: #E53935; font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # Add spacer to push buttons to the right
        layout.addStretch()
        
        # Always on top toggle
        self.pin_button = QPushButton("📌")
        self.pin_button.setToolTip("Toggle Always on Top")
        self.pin_button.setCheckable(True)
        self.pin_button.clicked.connect(self.toggle_always_on_top)
        layout.addWidget(self.pin_button)
        
        # Minimize button
        minimize_button = QPushButton("🗕")
        minimize_button.setToolTip("Minimize")
        minimize_button.clicked.connect(self.parent_window.showMinimized)
        layout.addWidget(minimize_button)
        
        # Close button
        close_button = QPushButton("✕")
        close_button.setObjectName("close_button")
        close_button.setToolTip("Close")
        close_button.clicked.connect(self.parent_window.close)
        layout.addWidget(close_button)
    
    def toggle_always_on_top(self, checked):
        """Toggle always-on-top window flag."""
        if not self.parent_window:
            return
            
        flags = self.parent_window.windowFlags()
        if checked:
            self.parent_window.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
            self.pin_button.setStyleSheet("background-color: #E53935; color: white;")
        else:
            self.parent_window.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
            self.pin_button.setStyleSheet("")
            
        self.parent_window.show()  # Need to show the window again after changing flags
    
    def mousePressEvent(self, event):
        """Handle mouse press for window dragging."""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.parent_window.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for window dragging."""
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.parent_window.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release for window dragging."""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()


class HomeTab(QWidget):
    """Home tab with logo and dependency status."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Animation properties
        self.logo_opacity = 0.0
        self.logo_position = 0
        
        # Timer for animation
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        
        # Initialize UI
        self.init_ui()
        
        # Start animations after a short delay
        QTimer.singleShot(100, self.start_animations)
    
    def init_ui(self):
        """Set up the home tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Logo label (animated)
        self.logo_label = QLabel("Infiltrate")
        self.logo_label.setObjectName("logoLabel")  # For stylesheet targeting
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet("""
            QLabel#logoLabel {
                color: #E53935;
                font-size: 36px;
                font-weight: bold;
                font-family: 'Century Gothic';
            }
        """)
        self.logo_label.setMinimumHeight(100)
        layout.addWidget(self.logo_label)
        
        # Dependencies table
        self.dependency_table = QTableWidget()
        self.dependency_table.setColumnCount(4)
        self.dependency_table.setHorizontalHeaderLabels(["Name", "Installed Version", "Latest Version", "Update Needed"])
        self.dependency_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.dependency_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.dependency_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.dependency_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.dependency_table.verticalHeader().setVisible(False)
        self.dependency_table.setAlternatingRowColors(True)
        self.dependency_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.dependency_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.dependency_table)
        
        # Update button
        self.update_button = QPushButton("Check for Updates")
        self.update_button.setObjectName("updateButton")  # For stylesheet targeting
        self.update_button.clicked.connect(self.check_for_updates)
        layout.addWidget(self.update_button, alignment=Qt.AlignRight)
        
        # Load dependencies
        self.load_dependencies()
    
    def load_dependencies(self):
        """Load and display dependency information."""
        # Get dependencies (in a real app, you'd check versions properly)
        dependencies = [
            DependencyInfo("Python", platform.python_version(), platform.python_version()),
            DependencyInfo("PyQt5", self.get_package_version("PyQt5"), self.get_package_version("PyQt5")),
            DependencyInfo("Pillow", self.get_package_version("Pillow"), "10.0.0"),  # Simulated newer version
            DependencyInfo("requests", self.get_package_version("requests"), self.get_package_version("requests"))
        ]
        
        # Fill the table
        self.dependency_table.setRowCount(len(dependencies))
        for i, dep in enumerate(dependencies):
            self.dependency_table.setItem(i, 0, QTableWidgetItem(dep.name))
            self.dependency_table.setItem(i, 1, QTableWidgetItem(dep.installed_version))
            self.dependency_table.setItem(i, 2, QTableWidgetItem(dep.latest_version))
            
            # Update needed?
            update_item = QTableWidgetItem()
            update_item.setTextAlignment(Qt.AlignCenter)
            if dep.update_needed:
                update_item.setText("Yes")
                update_item.setForeground(QColor("#E53935"))  # Use red accent color
            else:
                update_item.setText("No")
                update_item.setForeground(QColor("#4CAF50"))  # Use green color
                
            self.dependency_table.setItem(i, 3, update_item)
    
    def get_package_version(self, package_name):
        """Get the installed version of a package."""
        try:
            return pkg_resources.get_distribution(package_name).version
        except pkg_resources.DistributionNotFound:
            return "Not installed"
    
    def check_for_updates(self):
        """Open the updater window."""
        check_for_updates(self.window())
    
    def start_animations(self):
        """Start logo animations."""
        self.animation_timer.start(16)  # ~60 FPS
    
    def update_animation(self):
        """Update animation frames."""
        # Logo fade-in
        if self.logo_opacity < 1.0:
            self.logo_opacity += 0.025
            if self.logo_opacity > 1.0:
                self.logo_opacity = 1.0
                
            self.logo_label.setStyleSheet(f"""
                QLabel#logoLabel {{
                    color: #E53935;
                    font-size: 36px;
                    font-weight: bold;
                    font-family: 'Century Gothic';
                    opacity: {self.logo_opacity};
                }}
            """)
        
        # Logo slide-down
        if self.logo_position < 20:
            self.logo_position += 1
            self.logo_label.setContentsMargins(0, self.logo_position, 0, 20 - self.logo_position)
        
        # Stop animation when complete
        if self.logo_opacity >= 1.0 and self.logo_position >= 20:
            self.animation_timer.stop()


class ImageConverterTab(QWidget):
    """Tab for image conversion functionality."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_path = ""
        
        # Initialize UI
        self.init_ui()
    
    def init_ui(self):
        """Set up the image converter tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Central area with drop zone
        drop_area = QWidget()
        drop_area.setObjectName("dropArea")
        drop_area.setMinimumHeight(300)
        drop_area.setStyleSheet("""
            QWidget#dropArea {
                border: 2px dashed #323232;
                border-radius: 8px;
                background-color: #1A1A1A;
            }
            
            QWidget#dropArea:hover {
                border-color: #E53935;
            }
        """)
        
        # Enable drag and drop
        drop_area.setAcceptDrops(True)
        drop_area.dragEnterEvent = self.dragEnterEvent
        drop_area.dropEvent = self.dropEvent
        
        # Drop area layout
        drop_layout = QVBoxLayout(drop_area)
        
        # Add image icon
        add_image_label = QLabel()
        add_image_path = str(Path(__file__).parent.parent / "Content" / "Images" / "AddImage.png")
        add_pixmap = QPixmap(add_image_path)
        if not add_pixmap.isNull():
            add_pixmap = add_pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            add_image_label.setPixmap(add_pixmap)
            add_image_label.setAlignment(Qt.AlignCenter)
        else:
            # Fallback if image not found
            add_image_label.setText("➕")
            add_image_label.setAlignment(Qt.AlignCenter)
            add_image_label.setStyleSheet("font-size: 48px; color: #606060;")
            
        drop_layout.addWidget(add_image_label, alignment=Qt.AlignCenter)
        
        # Instruction label
        inst_label = QLabel("Paste, Drag-and-Drop, or Select the image you would like to convert.")
        inst_label.setAlignment(Qt.AlignCenter)
        inst_label.setStyleSheet("color: #808080;")
        drop_layout.addWidget(inst_label, alignment=Qt.AlignCenter)
        
        # Select file button
        select_button = QPushButton("Select Image")
        select_button.clicked.connect(self.open_file_dialog)
        drop_layout.addWidget(select_button, alignment=Qt.AlignCenter)
        
        # Add drop area to main layout
        layout.addWidget(drop_area)
        
        # Instructions for clipboard paste
        paste_label = QLabel("You can also paste an image from clipboard using Ctrl+V")
        paste_label.setAlignment(Qt.AlignCenter)
        paste_label.setStyleSheet("color: #808080; font-size: 9pt;")
        layout.addWidget(paste_label, alignment=Qt.AlignCenter)
        
        # Set focus so we can catch key events
        self.setFocusPolicy(Qt.StrongFocus)
    
    def open_file_dialog(self):
        """Open file dialog to select an image."""
        file_filter = "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp);;All Files (*)"
        image_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", file_filter
        )
        
        if image_path:
            self.process_image(image_path)
    
    def process_image(self, image_path: str):
        """Process the selected image."""
        self.image_path = image_path
        
        # Show conversion dialog
        show_conversion_dialog(self, image_path)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events for file dropping."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop events for file dropping."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if file_path:
                    self.process_image(file_path)
                    
    def keyPressEvent(self, event):
        """Handle keyboard events."""
        # Check for Ctrl+V (paste)
        if event.key() == Qt.Key_V and event.modifiers() & Qt.ControlModifier:
            self.paste_from_clipboard()
        else:
            super().keyPressEvent(event)
    
    def paste_from_clipboard(self):
        """Handle pasting image from clipboard."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            # Get image from clipboard
            image = clipboard.image()
            if not image.isNull():
                # Save to temporary file
                temp_path = Path(os.path.join(tempfile.gettempdir(), "infiltrate_clipboard.png"))
                image.save(str(temp_path), "PNG")
                
                # Process the image
                self.process_image(str(temp_path))
        else:
            QMessageBox.information(self, "No Image", "No image found in clipboard.")


class SettingsTab(QWidget):
    """Tab for application settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Default settings
        self.dark_theme = True
        self.animation_speed = 1.0  # Normal speed
        self.output_folder = str(Path.home() / "Pictures" / "Infiltrate")
        
        # Initialize UI
        self.init_ui()
    
    def init_ui(self):
        """Set up the settings tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Theme selection
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        
        self.theme_toggle = QCheckBox("Dark Mode")
        self.theme_toggle.setChecked(self.dark_theme)
        self.theme_toggle.stateChanged.connect(self.toggle_theme)
        theme_layout.addWidget(self.theme_toggle)
        theme_layout.addStretch()
        
        layout.addLayout(theme_layout)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #323232;")
        layout.addWidget(separator)
        
        # Animation speed
        anim_layout = QHBoxLayout()
        anim_layout.addWidget(QLabel("Animation Speed:"))
        
        self.anim_combo = QComboBox()
        self.anim_combo.addItems(["Slow", "Normal", "Fast", "Off"])
        self.anim_combo.setCurrentIndex(1)  # Default to Normal
        self.anim_combo.currentIndexChanged.connect(self.change_animation_speed)
        anim_layout.addWidget(self.anim_combo)
        anim_layout.addStretch()
        
        layout.addLayout(anim_layout)
        
        # Add separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet("background-color: #323232;")
        layout.addWidget(separator2)
        
        # Default output folder
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Default Output Folder:"))
        
        self.folder_edit = QLineEdit(self.output_folder)
        self.folder_edit.setReadOnly(True)
        folder_layout.addWidget(self.folder_edit, 1)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_output_folder)
        folder_layout.addWidget(self.browse_button)
        
        layout.addLayout(folder_layout)
        
        # Add spacer
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Reset to defaults button
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        layout.addWidget(self.reset_button, alignment=Qt.AlignRight)
    
    def toggle_theme(self, checked):
        """Toggle between dark and light theme."""
        self.dark_theme = checked
        # In a real app, you would apply the theme change here
        QMessageBox.information(self, "Theme Change", 
                               "Theme changes will take effect after restart.")
    
    def change_animation_speed(self, index):
        """Change the animation speed setting."""
        speeds = [0.5, 1.0, 2.0, 0.0]  # Slow, Normal, Fast, Off
        self.animation_speed = speeds[index]
        # In a real app, you would apply this change to animations
    
    def browse_output_folder(self):
        """Open folder dialog to select default output folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Default Output Folder", self.output_folder
        )
        
        if folder:
            self.output_folder = folder
            self.folder_edit.setText(folder)
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        # Set default values
        self.dark_theme = True
        self.animation_speed = 1.0
        self.output_folder = str(Path.home() / "Pictures" / "Infiltrate")
        
        # Update UI
        self.theme_toggle.setChecked(self.dark_theme)
        self.anim_combo.setCurrentIndex(1)  # Normal
        self.folder_edit.setText(self.output_folder)
        
        QMessageBox.information(self, "Settings Reset", 
                               "All settings have been reset to defaults.")


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint)
        
        self.setWindowTitle("Infiltrate")
        self.setMinimumSize(800, 600)
        
        # Center on screen
        screen_geo = QApplication.desktop().screenGeometry()
        x = (screen_geo.width() - self.width()) // 2
        y = (screen_geo.height() - self.height()) // 2
        self.move(x, y)
        
        # Initialize UI
        self.init_ui()
    
    def init_ui(self):
        """Set up the main window UI."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Add custom title bar
        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)
        
        # Tab widget for content
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.South)
        self.tab_widget.setDocumentMode(True)
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_tabs()
    
    def create_tabs(self):
        """Create and add tabs to the tab widget."""
        # Home tab
        home_tab = HomeTab()
        home_icon_path = str(Path(__file__).parent.parent / "Content" / "Images" / "Home.png")
        home_icon = QIcon(home_icon_path)
        self.tab_widget.addTab(home_tab, home_icon, "Home")
        
        # Image Converter tab
        converter_tab = ImageConverterTab()
        picture_icon_path = str(Path(__file__).parent.parent / "Content" / "Images" / "Picture.png")
        picture_icon = QIcon(picture_icon_path)
        self.tab_widget.addTab(converter_tab, picture_icon, "Image Converter")
        
        # Settings tab
        settings_tab = SettingsTab()
        settings_icon_path = str(Path(__file__).parent.parent / "Content" / "Images" / "Settings.png")
        settings_icon = QIcon(settings_icon_path)
        self.tab_widget.addTab(settings_tab, settings_icon, "Settings")
        
        # Resize tab icons
        for i in range(self.tab_widget.count()):
            self.tab_widget.setIconSize(QSize(24, 24))
            
    def keyPressEvent(self, event):
        """Handle keyboard events."""
        # Pass to current tab if it's the image converter
        current_tab = self.tab_widget.currentWidget()
        if isinstance(current_tab, ImageConverterTab) and event.key() == Qt.Key_V and event.modifiers() & Qt.ControlModifier:
            current_tab.paste_from_clipboard()
