#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Updater module for Infiltrate application.
Handles checking for updates and applying them.
"""

import os
import sys
import json
import time
import tempfile
import shutil
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from enum import Enum

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QDialog, QProgressBar, QApplication
)
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QRunnable, QThreadPool, pyqtSlot, QTimer, QPoint
from PyQt5.QtGui import QFont, QTextCursor

# For network operations
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class UpdaterStatus(Enum):
    """Status codes for the updater process."""
    IDLE = 0
    CHECKING = 1
    DOWNLOADING = 2
    INSTALLING = 3
    COMPLETED = 4
    FAILED = 5
    CANCELLED = 6
    PAUSED = 7


class UpdaterSignals(QObject):
    """Signals for the updater worker thread."""
    status_changed = pyqtSignal(UpdaterStatus, str)
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)  # Success flag, message


class UpdaterWorker(QRunnable):
    """Worker thread for checking and applying updates."""
    
    # Sample update manifest URL - in a real app, this would be your actual update server
    UPDATE_MANIFEST_URL = "https://example.com/infiltrate/manifest.json"
    
    def __init__(self):
        super().__init__()
        self.signals = UpdaterSignals()
        self.is_paused = False
        self.is_cancelled = False
        self.current_version = "1.0.0"  # This should come from your app config
        
    def pause(self):
        """Pause the update process."""
        self.is_paused = True
        self.signals.log.emit("Update process paused. Press Resume to continue.")
        self.signals.status_changed.emit(UpdaterStatus.PAUSED, "Paused")
        
    def resume(self):
        """Resume the update process."""
        self.is_paused = False
        self.signals.log.emit("Resuming update process...")
        
    def cancel(self):
        """Cancel the update process."""
        self.is_cancelled = True
        self.signals.log.emit("Update process cancelled.")
        self.signals.status_changed.emit(UpdaterStatus.CANCELLED, "Cancelled")
        self.signals.finished.emit(False, "Update cancelled by user")
    
    @pyqtSlot()
    def run(self):
        """Run the update process."""
        try:
            # Check for network library
            if not REQUESTS_AVAILABLE:
                self.signals.log.emit("Error: The requests library is not installed. Cannot check for updates.")
                self.signals.status_changed.emit(UpdaterStatus.FAILED, "Failed")
                self.signals.finished.emit(False, "Missing required library: requests")
                return
                
            # Step 1: Check for updates
            self.signals.status_changed.emit(UpdaterStatus.CHECKING, "Checking for updates...")
            self.signals.log.emit("Checking for updates...")
            
            # Simulate network delay
            self._wait_or_break(1.5)
            if self.is_cancelled:
                return
                
            try:
                # In a real app, this would be an actual network request
                # response = requests.get(self.UPDATE_MANIFEST_URL, timeout=10, verify=True)
                # manifest = response.json()
                
                # For demo purposes, we'll simulate a manifest
                manifest = self._get_simulated_manifest()
                
                self.signals.log.emit(f"Current version: {self.current_version}")
                self.signals.log.emit(f"Latest version: {manifest['version']}")
                
                # Compare versions
                if not self._is_update_needed(self.current_version, manifest['version']):
                    self.signals.log.emit("You are already running the latest version!")
                    self.signals.status_changed.emit(UpdaterStatus.COMPLETED, "Up to date")
                    self.signals.finished.emit(True, "Already up to date")
                    return
                    
                # Update is available
                self.signals.log.emit(f"Update available: {manifest['version']}")
                self.signals.log.emit(f"Changes: {manifest['changelog']}")
                
            except Exception as e:
                self.signals.log.emit(f"Error checking for updates: {str(e)}")
                self.signals.status_changed.emit(UpdaterStatus.FAILED, "Failed")
                self.signals.finished.emit(False, f"Update check failed: {str(e)}")
                return
            
            # Step 2: Download update
            self.signals.status_changed.emit(UpdaterStatus.DOWNLOADING, "Downloading update...")
            self.signals.log.emit("Downloading update...")
            
            try:
                # Simulate download with progress
                total_chunks = 10
                for i in range(total_chunks + 1):
                    if self.is_cancelled:
                        return
                        
                    while self.is_paused:
                        time.sleep(0.1)
                        if self.is_cancelled:
                            return
                    
                    progress = int((i / total_chunks) * 100)
                    self.signals.progress.emit(progress)
                    self.signals.log.emit(f"Downloading... {progress}%")
                    
                    # Simulate network delay
                    self._wait_or_break(0.3)
                
                self.signals.log.emit("Download completed!")
                
            except Exception as e:
                self.signals.log.emit(f"Error downloading update: {str(e)}")
                self.signals.status_changed.emit(UpdaterStatus.FAILED, "Failed")
                self.signals.finished.emit(False, f"Download failed: {str(e)}")
                return
            
            # Step 3: Install update
            self.signals.status_changed.emit(UpdaterStatus.INSTALLING, "Installing update...")
            self.signals.log.emit("Installing update...")
            
            try:
                # Simulate installation
                for i in range(5):
                    if self.is_cancelled:
                        return
                        
                    while self.is_paused:
                        time.sleep(0.1)
                        if self.is_cancelled:
                            return
                    
                    self.signals.log.emit(f"Installing component {i+1}/5...")
                    
                    # Simulate installation delay
                    self._wait_or_break(0.7)
                
                self.signals.log.emit("Installation completed!")
                
            except Exception as e:
                self.signals.log.emit(f"Error installing update: {str(e)}")
                self.signals.status_changed.emit(UpdaterStatus.FAILED, "Failed")
                self.signals.finished.emit(False, f"Installation failed: {str(e)}")
                return
            
            # Step 4: Finalize
            self.signals.status_changed.emit(UpdaterStatus.COMPLETED, "Updated")
            self.signals.log.emit(f"Update to version {manifest['version']} completed successfully!")
            self.signals.log.emit("Please restart the application to apply changes.")
            self.signals.finished.emit(True, "Update completed successfully")
            
        except Exception as e:
            self.signals.log.emit(f"Unexpected error during update: {str(e)}")
            self.signals.status_changed.emit(UpdaterStatus.FAILED, "Failed")
            self.signals.finished.emit(False, f"Update failed: {str(e)}")
    
    def _get_simulated_manifest(self) -> Dict[str, Any]:
        """Simulate fetching update manifest for demo purposes."""
        return {
            "version": "1.1.0",
            "min_required": "1.0.0",
            "download_url": "https://example.com/infiltrate/Infiltrate-1.1.0.zip",
            "changelog": "- Improved image conversion quality\n- Added WebP format support\n- Fixed UI bugs",
            "size": 15000000,  # Size in bytes
            "hash": "abcdef1234567890abcdef1234567890"  # SHA-256 hash
        }
    
    def _is_update_needed(self, current: str, latest: str) -> bool:
        """
        Compare version strings to determine if an update is needed.
        
        Args:
            current: Current version string (e.g., "1.0.0")
            latest: Latest version string (e.g., "1.1.0")
            
        Returns:
            True if latest version is newer than current, False otherwise
        """
        current_parts = [int(x) for x in current.split('.')]
        latest_parts = [int(x) for x in latest.split('.')]
        
        # Compare parts from left to right
        for i in range(max(len(current_parts), len(latest_parts))):
            current_part = current_parts[i] if i < len(current_parts) else 0
            latest_part = latest_parts[i] if i < len(latest_parts) else 0
            
            if latest_part > current_part:
                return True
            elif latest_part < current_part:
                return False
                
        # If we get here, versions are identical
        return False
    
    def _wait_or_break(self, seconds: float):
        """Wait for specified seconds, unless cancelled."""
        start_time = time.time()
        while time.time() - start_time < seconds:
            if self.is_cancelled:
                break
            if self.is_paused:
                # If paused, don't count this time
                start_time = time.time() - (time.time() - start_time)
            time.sleep(0.1)


class UpdaterWindow(QWidget):
    """Window that shows update progress and controls."""
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.parent_widget = parent
        self.threadpool = QThreadPool()
        self.worker = None
        
        self.setWindowTitle("Infiltrate Updater")
        self.setMinimumWidth(400)
        self.setMinimumHeight(250)
        
        # Shadow effect and border
        self.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                border: 1px solid #323232;
                border-radius: 4px;
            }
        """)
        
        # Initialize UI
        self.init_ui()
        
        # Position relative to parent
        self.position_window()
        
    def init_ui(self):
        """Set up the window UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)
        
        # Title bar with fixed label
        title_layout = QHBoxLayout()
        title_label = QLabel("Infiltrate Updater")
        title_label.setStyleSheet("font-weight: bold; color: #E53935;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #121212;
                border: 1px solid #323232;
                font-family: 'Century Gothic';
            }
        """)
        layout.addWidget(self.log_display)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.pause_resume_button = QPushButton("Pause")
        self.pause_resume_button.clicked.connect(self.toggle_pause_resume)
        button_layout.addWidget(self.pause_resume_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_update)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def position_window(self):
        """Position the updater window relative to parent."""
        if self.parent_widget:
            parent_geo = self.parent_widget.geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + 50  # Position near the top of parent
            self.move(x, y)
    
    def log(self, message: str):
        """Add a message to the log display."""
        self.log_display.append(message)
        # Scroll to bottom
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_display.setTextCursor(cursor)
    
    def start_update(self):
        """Start the update process."""
        # Clear previous log
        self.log_display.clear()
        self.progress_bar.setValue(0)
        
        # Create worker
        self.worker = UpdaterWorker()
        
        # Connect signals
        self.worker.signals.log.connect(self.log)
        self.worker.signals.progress.connect(self.progress_bar.setValue)
        self.worker.signals.status_changed.connect(self.update_status)
        self.worker.signals.finished.connect(self.on_update_finished)
        
        # Reset buttons
        self.pause_resume_button.setText("Pause")
        self.pause_resume_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        
        # Start the updater
        self.log("Starting update process...")
        self.threadpool.start(self.worker)
    
    def toggle_pause_resume(self):
        """Toggle between pause and resume."""
        if not self.worker:
            return
            
        if self.pause_resume_button.text() == "Pause":
            self.worker.pause()
            self.pause_resume_button.setText("Resume")
        else:
            self.worker.resume()
            self.pause_resume_button.setText("Pause")
    
    def cancel_update(self):
        """Cancel the update process."""
        if not self.worker:
            return
            
        self.worker.cancel()
        self.pause_resume_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
    
    def update_status(self, status: UpdaterStatus, message: str):
        """Update the window based on status change."""
        if status == UpdaterStatus.COMPLETED:
            self.pause_resume_button.setEnabled(False)
        elif status == UpdaterStatus.FAILED:
            self.pause_resume_button.setEnabled(False)
        elif status == UpdaterStatus.CANCELLED:
            self.pause_resume_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
    
    def on_update_finished(self, success: bool, message: str):
        """Handle update completion."""
        if success:
            self.log(f"Update finished: {message}")
            # In a real app, you might prompt for restart here
        else:
            self.log(f"Update failed: {message}")
        
        self.pause_resume_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        
        # Add a close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        self.layout().addWidget(close_button)


def check_for_updates(parent=None):
    """
    Open the updater window and start checking for updates.
    
    Args:
        parent: Parent widget
    """
    updater = UpdaterWindow(parent)
    updater.show()
    updater.start_update()
    return updater
