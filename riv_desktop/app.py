import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog, QSlider,
                            QToolBar, QStyle, QFrame, QSizePolicy, QDialog)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon, QAction
from oct_viewer import OCTModel, Tool
import qtawesome as qta
from s3_browser import S3Browser
import os

class OCTViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.model = OCTModel()
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("OCT Scan Viewer")
        self.setMinimumSize(800, 400)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create navigation menu
        nav_bar = self._create_nav_bar()
        main_layout.addWidget(nav_bar)
        
        # Create content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(5)
        main_layout.addWidget(content_widget)
        
        # Create image display area with horizontal layout for side-by-side viewing
        image_layout = QHBoxLayout()
        image_layout.setSpacing(10)
        
        # Main image container with clear button
        main_container = QWidget()
        main_container_layout = QVBoxLayout(main_container)
        main_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header for main image with clear button
        main_header = QHBoxLayout()
        main_header.addStretch()
        self.clear_main_button = QPushButton()
        self.clear_main_button.setIcon(qta.icon('fa5s.minus-circle', color='#ffffff'))
        self.clear_main_button.setIconSize(QSize(16, 16))
        self.clear_main_button.setFixedSize(24, 24)
        self.clear_main_button.clicked.connect(self.clear_main_image)
        self.clear_main_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 12px;
                margin: 5px;
                position: absolute;
                top: 5px;
                right: 5px;
            }
            QPushButton:hover {
                background-color: #3b3b3b;
            }
            QPushButton:pressed {
                background-color: #454545;
            }
        """)
        main_header.addWidget(self.clear_main_button)
        main_container_layout.addLayout(main_header)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(300, 300)  # Set minimum size
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  # Allow expansion
        main_container_layout.addWidget(self.image_label)
        image_layout.addWidget(main_container, 1)  # Add stretch factor
        
        # Comparison image container with clear button
        comparison_container = QWidget()
        comparison_container_layout = QVBoxLayout(comparison_container)
        comparison_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header for comparison image with clear button
        comparison_header = QHBoxLayout()
        comparison_header.addStretch()
        self.clear_comparison_button = QPushButton()
        self.clear_comparison_button.setIcon(qta.icon('fa5s.minus-circle', color='#ffffff'))
        self.clear_comparison_button.setIconSize(QSize(16, 16))
        self.clear_comparison_button.setFixedSize(24, 24)
        self.clear_comparison_button.clicked.connect(self.clear_comparison_image)
        self.clear_comparison_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 12px;
                margin: 5px;
                position: absolute;
                top: 5px;
                right: 5px;
            }
            QPushButton:hover {
                background-color: #3b3b3b;
            }
            QPushButton:pressed {
                background-color: #454545;
            }
        """)
        comparison_header.addWidget(self.clear_comparison_button)
        comparison_container_layout.addLayout(comparison_header)
        
        self.comparison_label = QLabel()
        self.comparison_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.comparison_label.setMinimumSize(300, 300)  # Set minimum size
        self.comparison_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  # Allow expansion
        comparison_container_layout.addWidget(self.comparison_label)
        comparison_container.hide()  # Hidden by default
        image_layout.addWidget(comparison_container, 1)  # Add stretch factor
        self.comparison_container = comparison_container  # Store reference
        
        content_layout.addLayout(image_layout)
        
        # Bottom controls container
        bottom_container = QWidget()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(2)
        
        # Create slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setEnabled(False)
        self.slider.valueChanged.connect(self.update_slice)
        bottom_layout.addWidget(self.slider)
        
        # Create slice info label
        self.info_label = QLabel("No file loaded")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(self.info_label)
        
        content_layout.addWidget(bottom_container)
        
        # Set content area to expand
        main_layout.setStretch(1, 1)

        # Set dark theme for entire application
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                color: #ffffff;
                background-color: #3b3b3b;
                border: none;
                padding: 5px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #454545;
            }
            QPushButton:pressed {
                background-color: #505050;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #3b3b3b;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #5c5c5c;
                border: 1px solid #999999;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
        """)

        # Create buttons
        button_layout = QHBoxLayout()
        
        # Local file button
        self.load_button = QPushButton("Load DICOM File")
        self.load_button.clicked.connect(self.load_dicom)
        button_layout.addWidget(self.load_button)
        
        # S3 browser button
        self.s3_button = QPushButton("Browse S3")
        self.s3_button.clicked.connect(self._handle_s3)
        button_layout.addWidget(self.s3_button)
        
        # Add button layout to main layout
        content_layout.addLayout(button_layout)

    def _create_nav_bar(self):
        nav_widget = QFrame()
        nav_widget.setFrameStyle(QFrame.Shape.NoFrame)
        nav_widget.setMaximumWidth(50)
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setSpacing(2)
        nav_layout.setContentsMargins(5, 5, 5, 5)

        # Create navigation buttons with modern icons
        nav_buttons = [
            ("File", "fa5s.folder-open", self._handle_file),
            ("Compare", "fa5s.columns", self._handle_compare),
            ("Annotate", "fa5s.draw-polygon", self._handle_annotate),
            ("Tag", "fa5s.tags", self._handle_tag)
        ]

        for text, icon_name, handler in nav_buttons:
            button = QPushButton()
            button.setIcon(qta.icon(icon_name, color='#ffffff'))
            button.setIconSize(QSize(20, 20))
            button.setFixedSize(40, 40)
            button.setToolTip(text)
            button.clicked.connect(handler)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #2b2b2b;
                    border: none;
                    border-radius: 5px;
                    padding: 0px;
                    margin: 0px auto;
                }
                QPushButton:hover {
                    background-color: #3b3b3b;
                }
                QPushButton:pressed {
                    background-color: #454545;
                }
                QToolTip {
                    background-color: #2b2b2b;
                    color: white;
                    border: 1px solid #3b3b3b;
                    border-radius: 4px;
                    padding: 4px;
                }
            """)
            nav_layout.addWidget(button, 0, Qt.AlignmentFlag.AlignCenter)

        # Add stretch to push buttons to top
        nav_layout.addStretch()
        
        # Style the navigation bar
        nav_widget.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border-right: 1px solid #3b3b3b;
            }
        """)
        
        return nav_widget

    def _handle_file(self):
        dialog = S3Browser(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            success, filepath = dialog.get_selected_file()
            if success:
                success, error = self.model.load_file(filepath)
                if success:
                    # Configure slider
                    num_slices = self.model.get_total_slices()
                    self.slider.setMinimum(0)
                    self.slider.setMaximum(num_slices - 1)
                    self.slider.setValue(0)
                    self.slider.setEnabled(True)
                    
                    self.update_slice(0)
                    
                    # Hide comparison view if showing
                    self.comparison_container.hide()
                else:
                    self.info_label.setText(f"Error loading file: {error}")
                
                # Clean up temporary file
                try:
                    os.remove(filepath)
                except:
                    pass

    def _handle_compare(self):
        if not self.model.dicom_data:
            self.info_label.setText("Please load a primary scan first")
            return

        dialog = S3Browser(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            success, filepath = dialog.get_selected_file()
            if success:
                success, error = self.model.load_comparison_file(filepath)
                if success:
                    self.comparison_container.show()
                    self.update_slice(self.slider.value())
                else:
                    self.info_label.setText(f"Error loading comparison: {error}")
                
                # Clean up temporary file
                try:
                    os.remove(filepath)
                except:
                    pass

    def _handle_annotate(self):
        self.model.set_active_tool(Tool.ANNOTATE)

    def _handle_tag(self):
        self.model.set_active_tool(Tool.TAG)

    def update_slice(self, slice_num):
        # Update main image
        q_image = self.model.get_slice_image(slice_num)
        if q_image is None:
            return
            
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)
        
        # Update comparison image if available
        if self.model.has_comparison():
            q_image = self.model.get_comparison_slice_image(slice_num)
            if q_image is not None:
                pixmap = QPixmap.fromImage(q_image)
                scaled_pixmap = pixmap.scaled(
                    self.comparison_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.comparison_label.setPixmap(scaled_pixmap)
        
        # Update info label
        total_slices = self.model.get_total_slices()
        self.info_label.setText(f"Slice {slice_num + 1} of {total_slices}")

    def clear_main_image(self):
        self.model.dicom_data = None
        self.image_label.clear()
        self.slider.setEnabled(False)
        self.info_label.setText("No file loaded")
        self.comparison_container.hide()  # Hide comparison when main is cleared

    def clear_comparison_image(self):
        self.model.comparison_data = None
        self.comparison_container.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update images when window is resized
        if hasattr(self, 'slider'):
            self.update_slice(self.slider.value())

    def load_dicom(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select DICOM file",
            "",
            "DICOM Files (*.dcm);;All Files (*)"
        )
        
        if filename:
            success, error = self.model.load_file(filename)
            if success:
                # Configure slider
                num_slices = self.model.get_total_slices()
                self.slider.setMinimum(0)
                self.slider.setMaximum(num_slices - 1)
                self.slider.setValue(0)
                self.slider.setEnabled(True)
                
                self.update_slice(0)
                
                # Hide comparison view if showing
                self.comparison_container.hide()
            else:
                self.info_label.setText(f"Error loading file: {error}")

    def _handle_s3(self):
        dialog = S3Browser(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            success, filepath = dialog.get_selected_file()
            if success:
                success, error = self.model.load_file(filepath)
                if success:
                    # Configure slider
                    num_slices = self.model.get_total_slices()
                    self.slider.setMinimum(0)
                    self.slider.setMaximum(num_slices - 1)
                    self.slider.setValue(0)
                    self.slider.setEnabled(True)
                    
                    self.update_slice(0)
                    
                    # Hide comparison view if showing
                    self.comparison_container.hide()
                else:
                    self.info_label.setText(f"Error loading file: {error}")
                
                # Clean up temporary file
                try:
                    os.remove(filepath)
                except:
                    pass

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern looking style
    viewer = OCTViewer()
    viewer.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()