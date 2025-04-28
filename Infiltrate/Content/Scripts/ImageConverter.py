#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ImageConverter module for Infiltrate application.
Handles conversion of images between various formats.
"""

import os
import sys
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Tuple, Dict
import time

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFileDialog, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QRunnable, QThreadPool, pyqtSlot
from PyQt5.QtGui import QPixmap, QImage

# Import Pillow for image processing
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


class ImageFormat(Enum):
    """Supported image formats for conversion."""
    PNG = "PNG"
    JPEG = "JPEG"
    BMP = "BMP"
    TIFF = "TIFF"
    GIF = "GIF"
    WEBP = "WEBP"
    ICO = "ICO"


class ConversionSignals(QObject):
    """Signals used for communicating conversion progress and completion."""
    started = pyqtSignal()
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)  # Success flag, message
    error = pyqtSignal(str)


class ConversionWorker(QRunnable):
    """Worker thread for performing image conversion."""
    
    def __init__(self, input_path: str, output_format: str, output_path: str):
        super().__init__()
        self.input_path = input_path
        self.output_format = output_format
        self.output_path = output_path
        self.signals = ConversionSignals()
        
    @pyqtSlot()
    def run(self):
        """Execute the conversion task."""
        try:
            self.signals.started.emit()
            
            # Check if Pillow is available
            if not PILLOW_AVAILABLE:
                self.signals.error.emit("Pillow library is not installed. Cannot perform conversion.")
                return
                
            # Open the image
            try:
                img = Image.open(self.input_path)
            except Exception as e:
                self.signals.error.emit(f"Failed to open image: {str(e)}")
                return
                
            # Set progress to 30%
            self.signals.progress.emit(30)
            
            # Convert and save
            try:
                # If output format is JPEG and the image has alpha channel, convert to RGB
                if self.output_format == "JPEG" and img.mode == "RGBA":
                    img = img.convert("RGB")
                
                # If target is same as source, just copy
                if Path(self.input_path).suffix.lower() == f".{self.output_format.lower()}" and self.input_path != self.output_path:
                    # Just a copy operation
                    img.save(self.output_path)
                else:
                    # Actual conversion
                    img.save(self.output_path, format=self.output_format)
                
                # Set progress to 90%
                self.signals.progress.emit(90)
                
                # Small delay to show progress
                time.sleep(0.3)
                
                # Complete
                self.signals.progress.emit(100)
                self.signals.finished.emit(True, f"Successfully converted to {self.output_format}")
                
            except Exception as e:
                self.signals.error.emit(f"Failed to convert image: {str(e)}")
                
        except Exception as e:
            self.signals.error.emit(f"Unexpected error: {str(e)}")


class ConversionDialog(QDialog):
    """Dialog for image conversion options and progress."""
    
    def __init__(self, parent=None, image_path: str = ""):
        super().__init__(parent)
        self.image_path = image_path
        self.output_path = ""
        self.threadpool = QThreadPool()
        
        self.setWindowTitle("Convert Image")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        
        # Initialize UI
        self.init_ui()
        
    def init_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Image preview (small thumbnail)
        self.preview_label = QLabel("Image Preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.load_preview()
        layout.addWidget(self.preview_label)
        
        # Format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        
        self.format_combo = QComboBox()
        for fmt in ImageFormat:
            self.format_combo.addItem(fmt.value)
        
        # Select appropriate format based on input file extension
        input_ext = Path(self.image_path).suffix.lower().lstrip('.')
        for i, fmt in enumerate(ImageFormat):
            if fmt.value.lower() == input_ext:
                self.format_combo.setCurrentIndex(i)
                break
        
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)
        
        # Output path selection
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Output Path:"))
        
        self.path_label = QLabel("Not selected")
        self.path_label.setWordWrap(True)
        path_layout.addWidget(self.path_label, 1)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_output)
        path_layout.addWidget(self.browse_button)
        
        layout.addLayout(path_layout)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.convert_button = QPushButton("Convert")
        self.convert_button.clicked.connect(self.start_conversion)
        self.convert_button.setEnabled(False)  # Disabled until output path is selected
        button_layout.addWidget(self.convert_button)
        
        layout.addLayout(button_layout)
    
    def load_preview(self):
        """Load and display a thumbnail preview of the image."""
        try:
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                # Scale down to a reasonable thumbnail size while maintaining aspect ratio
                pixmap = pixmap.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(pixmap)
            else:
                self.preview_label.setText("Unable to load preview")
        except Exception as e:
            self.preview_label.setText(f"Preview error: {str(e)}")
    
    def browse_output(self):
        """Open file dialog to select output path."""
        # Get the selected format
        selected_format = self.format_combo.currentText()
        extension = selected_format.lower()
        
        # Prepare default name based on input file
        input_path = Path(self.image_path)
        default_name = f"{input_path.stem}.{extension}"
        
        # Open save file dialog
        file_filter = f"{selected_format} Files (*.{extension})"
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Converted Image", default_name, file_filter
        )
        
        if output_path:
            self.output_path = output_path
            self.path_label.setText(output_path)
            self.convert_button.setEnabled(True)
    
    def start_conversion(self):
        """Start the conversion process in a separate thread."""
        if not self.output_path:
            QMessageBox.warning(self, "Missing Output Path", "Please select an output path.")
            return
        
        # Create worker
        selected_format = self.format_combo.currentText()
        worker = ConversionWorker(self.image_path, selected_format, self.output_path)
        
        # Connect signals
        worker.signals.started.connect(self.on_conversion_started)
        worker.signals.progress.connect(self.on_progress_update)
        worker.signals.finished.connect(self.on_conversion_finished)
        worker.signals.error.connect(self.on_conversion_error)
        
        # Start the conversion
        self.threadpool.start(worker)
    
    def on_conversion_started(self):
        """Handle conversion started signal."""
        self.progress_bar.setVisible(True)
        self.convert_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.status_label.setText("Converting image...")
    
    def on_progress_update(self, value):
        """Update the progress bar."""
        self.progress_bar.setValue(value)
    
    def on_conversion_finished(self, success, message):
        """Handle conversion completion."""
        if success:
            self.status_label.setText(message)
            self.progress_bar.setValue(100)
            
            # Show success message
            QMessageBox.information(self, "Conversion Complete", message)
            self.accept()  # Close the dialog
        else:
            self.on_conversion_error(message)
    
    def on_conversion_error(self, error_message):
        """Handle conversion errors."""
        self.status_label.setText(f"Error: {error_message}")
        self.progress_bar.setVisible(False)
        self.convert_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        
        # Show error message
        QMessageBox.critical(self, "Conversion Error", error_message)


def convert_image(input_path: str, output_format: str, output_path: str, progress_callback: Optional[Callable[[int], None]] = None) -> Tuple[bool, str]:
    """
    Convert an image from one format to another.
    
    Args:
        input_path: Path to the input image
        output_format: Target format (from ImageFormat enum)
        output_path: Path where to save the converted image
        progress_callback: Optional callback for reporting progress
        
    Returns:
        Tuple of (success flag, message)
    """
    try:
        # Check if Pillow is available
        if not PILLOW_AVAILABLE:
            return False, "Pillow library is not installed. Cannot perform conversion."
            
        # Open the image
        img = Image.open(input_path)
        
        if progress_callback:
            progress_callback(30)
        
        # Convert and save
        if output_format == "JPEG" and img.mode == "RGBA":
            img = img.convert("RGB")
            
        img.save(output_path, format=output_format)
        
        if progress_callback:
            progress_callback(100)
            
        return True, f"Successfully converted to {output_format}"
        
    except Exception as e:
        return False, f"Conversion failed: {str(e)}"


def show_conversion_dialog(parent, image_path: str) -> bool:
    """
    Show the conversion dialog and handle the image conversion.
    
    Args:
        parent: Parent widget
        image_path: Path to the input image
        
    Returns:
        True if conversion was successful, False otherwise
    """
    dialog = ConversionDialog(parent, image_path)
    result = dialog.exec_()
    return result == QDialog.Accepted
