import os
import sys
from pathlib import Path
from PIL import Image
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QFileDialog, QComboBox, QFrame, QDialog, QLineEdit,
                            QProgressBar, QMessageBox, QApplication)
from PyQt5.QtGui import QIcon, QPixmap, QFont, QDrag, QImage, QPalette, QColor, QGuiApplication
from PyQt5.QtCore import Qt, QSize, QMimeData, QUrl, QRect, QPropertyAnimation, QEasingCurve, pyqtSignal


class ImageFormatDialog(QDialog):
    """Custom dialog for selecting image conversion options"""
    
    def __init__(self, parent=None, original_format=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
                border: 1px solid #333333;
                border-radius: 10px;
            }
            QLabel {
                color: #FFFFFF;
                font-family: 'Century Gothic';
            }
            QComboBox {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #333333;
                padding: 5px;
                border-radius: 4px;
                font-family: 'Century Gothic';
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(dropdown.png);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #1E1E1E;
                color: #FFFFFF;
                selection-background-color: #E63946;
            }
            QLineEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #333333;
                padding: 5px;
                border-radius: 4px;
                font-family: 'Century Gothic';
            }
            QPushButton {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-family: 'Century Gothic';
            }
            QPushButton:hover {
                background-color: #E63946;
            }
            QPushButton:pressed {
                background-color: #C1121F;
            }
        """)
        
        self.setMinimumWidth(400)
        self.original_format = original_format
        self.selected_format = None
        self.output_path = None
        self.dragging = False
        self.dragPos = None
        
        self.init_ui()
    
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Convert Image")
        title_label.setFont(QFont("Century Gothic", 16, QFont.Bold))
        title_label.setStyleSheet("color: #E63946;")
        title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title_label)
        
        # Format selection
        format_layout = QHBoxLayout()
        format_label = QLabel("Target Format:")
        self.format_combo = QComboBox()
        
        # Add all supported formats
        supported_formats = ["PNG", "JPEG", "BMP", "GIF", "TIFF", "WEBP", "ICO", "PPM"]
        
        # If we have an original format, put it at the beginning
        if self.original_format and self.original_format.upper() in supported_formats:
            supported_formats.remove(self.original_format.upper())
        
        self.format_combo.addItems(supported_formats)
        
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        self.layout.addLayout(format_layout)
        
        # Output path
        path_layout = QHBoxLayout()
        path_label = QLabel("Save to:")
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("Select output location...")
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_output)
        
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_btn)
        self.layout.addLayout(path_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.convert_btn = QPushButton("Convert")
        self.convert_btn.setEnabled(False)  # Disable until path is selected
        self.convert_btn.clicked.connect(self.accept_conversion)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.convert_btn)
        self.layout.addLayout(button_layout)
    
    def browse_output(self):
        selected_format = self.format_combo.currentText().lower()
        file_filter = f"{selected_format.upper()} Files (*.{selected_format})"
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Converted Image", "", file_filter
        )
        
        if filename:
            # Make sure the filename has the correct extension
            if not filename.lower().endswith(f".{selected_format}"):
                filename += f".{selected_format}"
            
            self.path_edit.setText(filename)
            self.output_path = filename
            self.convert_btn.setEnabled(True)
    
    def accept_conversion(self):
        self.selected_format = self.format_combo.currentText().lower()
        super().accept()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.dragPos = event.globalPos()
    
    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False


class ConversionProgressDialog(QDialog):
    """Dialog showing conversion progress"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
                border: 1px solid #333333;
                border-radius: 10px;
            }
            QLabel {
                color: #FFFFFF;
                font-family: 'Century Gothic';
            }
            QProgressBar {
                border: none;
                background-color: #1E1E1E;
                color: #FFFFFF;
                text-align: center;
                font-family: 'Century Gothic';
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: #E63946;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-family: 'Century Gothic';
            }
            QPushButton:hover {
                background-color: #E63946;
            }
            QPushButton:pressed {
                background-color: #C1121F;
            }
        """)
        
        self.setMinimumWidth(350)
        self.init_ui()
    
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # Status label
        self.status_label = QLabel("Converting image...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.layout.addWidget(self.progress)
        
        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.layout.addWidget(self.cancel_btn, alignment=Qt.AlignCenter)
    
    def set_progress(self, value):
        self.progress.setValue(value)
    
    def set_status(self, text):
        self.status_label.setText(text)


class ImageConverterWidget(QWidget):
    """Main widget for the Image Converter tab"""
    image_dropped = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Initialize variables
        self.current_image_path = None
        self.current_pixmap = None
        
        # Initialize UI
        self.init_ui()
        
        # Connect signals
        self.image_dropped.connect(self.load_image)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignCenter)
        
        # Drop area frame
        self.drop_area = QFrame()
        self.drop_area.setFrameShape(QFrame.StyledPanel)
        self.drop_area.setMinimumSize(400, 300)
        self.drop_area.setSizePolicy(QApplication.instance().setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.drop_area.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A;
                border: 2px dashed #333333;
                border-radius: 10px;
            }
        """)
        
        drop_layout = QVBoxLayout(self.drop_area)
        drop_layout.setAlignment(Qt.AlignCenter)
        
        # Add image icon
        images_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Content', 'Images')
        add_image_pixmap = QPixmap(os.path.join(images_dir, 'AddImage.png'))
        
        # Darken the image
        darkened_image = QImage(add_image_pixmap.size(), QImage.Format_ARGB32)
        darkened_image.fill(Qt.transparent)
        
        p = QPalette()
        p.setColor(QPalette.Window, QColor(0, 0, 0, 128))
        
        self.add_image_label = QLabel()
        self.add_image_label.setPixmap(add_image_pixmap.scaled(
            100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        self.add_image_label.setAlignment(Qt.AlignCenter)
        self.add_image_label.setGraphicsEffect(self.create_darkening_effect(0.3))
        
        # Instructions label
        self.instructions_label = QLabel("Paste, Drop, or Select the image you would like to convert")
        self.instructions_label.setAlignment(Qt.AlignCenter)
        self.instructions_label.setFont(QFont("Century Gothic", 12))
        self.instructions_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        
        # Select file button
        self.select_btn = QPushButton("Select Image")
        self.select_btn.setFont(QFont("Century Gothic", 10))
        self.select_btn.clicked.connect(self.open_file_dialog)
        
        # Add widgets to drop area
        drop_layout.addWidget(self.add_image_label)
        drop_layout.addWidget(self.instructions_label)
        drop_layout.addWidget(self.select_btn, alignment=Qt.AlignCenter)
        
        # Convert button (initially hidden)
        self.convert_btn = QPushButton("Convert Image")
        self.convert_btn.setFont(QFont("Century Gothic", 12))
        self.convert_btn.setFixedWidth(200)
        self.convert_btn.clicked.connect(self.convert_image)
        self.convert_btn.setVisible(False)
        
        # Add widgets to main layout
        layout.addWidget(self.drop_area)
        layout.addWidget(self.convert_btn, alignment=Qt.AlignCenter)
    
    def create_darkening_effect(self, opacity):
        effect = QGraphicsOpacityEffect()
        effect.setOpacity(opacity)
        return effect
    
    def dragEnterEvent(self, event):
        # Check if the drag contains image data
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if self.is_valid_image_file(file_path):
                        event.acceptProposedAction()
                        self.drop_area.setStyleSheet("""
                            QFrame {
                                background-color: #2A2A2A;
                                border: 2px dashed #E63946;
                                border-radius: 10px;
                            }
                        """)
                        return
        
        event.ignore()
    
    def dragLeaveEvent(self, event):
        self.drop_area.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A;
                border: 2px dashed #333333;
                border-radius: 10px;
            }
        """)
        event.accept()
    
    def dropEvent(self, event):
        self.drop_area.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A;
                border: 2px dashed #333333;
                border-radius: 10px;
            }
        """)
        
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if self.is_valid_image_file(file_path):
                        self.image_dropped.emit(file_path)
                        event.acceptProposedAction()
                        return
        
        event.ignore()
    
    def is_valid_image_file(self, file_path):
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp', '.ico']
        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in valid_extensions
    
    def open_file_dialog(self):
        file_filter = "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp *.ico)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", file_filter
        )
        
        if file_path:
            self.load_image(file_path)
    
    def load_image(self, file_path):
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError("Image file not found.")
            
            # Load and display the image
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                raise ValueError("Failed to load image.")
            
            # Clear the drop area
            for i in reversed(range(self.drop_area.layout().count())):
                widget = self.drop_area.layout().itemAt(i).widget()
                if widget:
                    widget.deleteLater()
            
            # Create a label to display the image
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignCenter)
            
            # Scale the pixmap to fit in the drop area while preserving aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.drop_area.width() - 40,
                self.drop_area.height() - 40,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            image_label.setPixmap(scaled_pixmap)
            self.drop_area.layout().addWidget(image_label)
            
            # Store the current image
            self.current_image_path = file_path
            self.current_pixmap = pixmap
            
            # Show the convert button
            self.convert_btn.setVisible(True)
            
            # Animate the new content
            self.animate_content_change()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image: {str(e)}")
    
    def animate_content_change(self):
        # Create animation for the convert button
        anim = QPropertyAnimation(self.convert_btn, b"geometry")
        anim.setDuration(500)
        anim.setStartValue(QRect(
            self.convert_btn.x(),
            self.convert_btn.y() + 50,
            self.convert_btn.width(),
            self.convert_btn.height()
        ))
        anim.setEndValue(self.convert_btn.geometry())
        anim.setEasingCurve(QEasingCurve.OutBack)
        anim.start()
    
    def convert_image(self):
        if not self.current_image_path:
            return
        
        try:
            # Get the original format
            original_format = os.path.splitext(self.current_image_path)[1][1:].lower()
            
            # Show the format selection dialog
            dialog = ImageFormatDialog(self, original_format)
            result = dialog.exec_()
            
            if result == QDialog.Accepted and dialog.selected_format and dialog.output_path:
                # Show progress dialog
                progress_dialog = ConversionProgressDialog(self)
                progress_dialog.show()
                
                # Perform conversion
                try:
                    # Load the image
                    progress_dialog.set_status("Loading image...")
                    progress_dialog.set_progress(10)
                    QApplication.processEvents()
                    
                    # Open the image with PIL
                    img = Image.open(self.current_image_path)
                    
                    # Update progress
                    progress_dialog.set_status("Converting image...")
                    progress_dialog.set_progress(40)
                    QApplication.processEvents()
                    
                    # Convert and save the image
                    target_format = dialog.selected_format.upper()
                    if target_format == "JPG":
                        target_format = "JPEG"  # PIL uses JPEG, not JPG
                    
                    # For some formats, we need to handle transparency
                    if target_format in ["JPEG", "BMP"] and img.mode == "RGBA":
                        # Create a white background
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
                        background.save(dialog.output_path, target_format)
                    else:
                        img.save(dialog.output_path, target_format)
                    
                    # Update progress
                    progress_dialog.set_status("Conversion complete!")
                    progress_dialog.set_progress(100)
                    QApplication.processEvents()
                    
                    # Close progress dialog after a short delay
                    QTimer.singleShot(1000, progress_dialog.accept)
                    
                    # Show success message
                    QMessageBox.information(
                        self, 
                        "Conversion Complete", 
                        f"Image successfully converted to {dialog.selected_format.upper()} format."
                    )
                    
                except Exception as e:
                    progress_dialog.accept()
                    QMessageBox.critical(self, "Conversion Error", f"Error during conversion: {str(e)}")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to convert image: {str(e)}")
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        # If an image is displayed, rescale it
        if self.current_pixmap:
            for i in range(self.drop_area.layout().count()):
                widget = self.drop_area.layout().itemAt(i).widget()
                if isinstance(widget, QLabel) and widget.pixmap():
                    scaled_pixmap = self.current_pixmap.scaled(
                        self.drop_area.width() - 40,
                        self.drop_area.height() - 40,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    widget.setPixmap(scaled_pixmap)
    
    def keyPressEvent(self, event):
        # Handle paste event
        if event.matches(QKeySequence.Paste):
            clipboard = QGuiApplication.clipboard()
            mime_data = clipboard.mimeData()
            
            if mime_data.hasImage():
                pixmap = QPixmap(clipboard.image())
                
                if not pixmap.isNull():
                    # Save the pixmap to a temporary file
                    temp_dir = os.path.join(os.path.expanduser("~"), "Infiltrate", "temp")
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    temp_file = os.path.join(temp_dir, "clipboard_image.png")
                    pixmap.save(temp_file, "PNG")
                    
                    # Load the saved image
                    self.load_image(temp_file)
        
        super().keyPressEvent(event)
