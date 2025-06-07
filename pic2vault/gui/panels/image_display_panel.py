# image_display_panel.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QDialog, QSlider, QLabel
from PyQt5.QtCore import Qt
from gui.widgets.zoomable_image_view import ZoomableImageView
import cv2
import os
import numpy as np

class ImageDisplayPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.image_view = ZoomableImageView()
        self.current_image_path = None
        self.current_image_cv = None
        self.original_image_cv = None
        self.edit_dialog = None

        # Buttons
        self.rotate_button = QPushButton("🔄 Rotate 90°")
        self.rotate_button.clicked.connect(self.rotate_image)

        self.save_button = QPushButton("💾 Save")
        self.save_button.clicked.connect(self.save_image)

        self.edit_button = QPushButton("🛠️ Edit")
        self.edit_button.clicked.connect(self.open_edit_dialog)

        self.reset_button = QPushButton("♻️ Reset")
        self.reset_button.clicked.connect(self.reset_image)

        tool_layout = QHBoxLayout()
        tool_layout.addWidget(self.rotate_button)
        tool_layout.addWidget(self.save_button)
        tool_layout.addWidget(self.edit_button)
        tool_layout.addWidget(self.reset_button)

        layout = QVBoxLayout()
        layout.addWidget(self.image_view)
        layout.addLayout(tool_layout)
        self.setLayout(layout)

    def load_image(self, path):
        if self.edit_dialog:
            self.edit_dialog.close()
        self.current_image_path = path
        self.current_image_cv = cv2.imread(path)
        if self.current_image_cv is not None:
            self.original_image_cv = self.current_image_cv.copy()
            rgb_image = cv2.cvtColor(self.current_image_cv, cv2.COLOR_BGR2RGB)
            self.image_view.load_cv_array(rgb_image, fit_to_view=True)

    def rotate_image(self):
        if self.current_image_cv is not None:
            self.current_image_cv = cv2.rotate(self.current_image_cv, cv2.ROTATE_90_CLOCKWISE)
            rgb_image = cv2.cvtColor(self.current_image_cv, cv2.COLOR_BGR2RGB)
            self.image_view.load_cv_array(rgb_image)

    def save_image(self):
        if self.current_image_cv is not None and self.current_image_path:
            cv2.imwrite(self.current_image_path, self.current_image_cv)
            self.parent.statusBar().showMessage(f"Image saved: {os.path.basename(self.current_image_path)}")
            if self.edit_dialog:
                self.edit_dialog.close()

    def reset_image(self):
        if self.original_image_cv is not None:
            self.current_image_cv = self.original_image_cv.copy()
            rgb_image = cv2.cvtColor(self.current_image_cv, cv2.COLOR_BGR2RGB)
            self.image_view.load_cv_array(rgb_image, fit_to_view=True)
            self.parent.statusBar().showMessage("Image reset to original")
            if self.edit_dialog:
                self.edit_dialog.close()

    def open_edit_dialog(self):
        if self.current_image_cv is None:
            return

        if self.edit_dialog:
            self.edit_dialog.close()

        self.edit_dialog = QDialog(self, Qt.Window)
        self.edit_dialog.setWindowTitle("Photo Adjustments")
        self.edit_dialog.setMinimumWidth(300)
        self.edit_dialog.setModal(False)

        layout = QVBoxLayout()

        brightness_label = QLabel("Brightness")
        brightness_slider = QSlider(Qt.Horizontal)
        brightness_slider.setMinimum(-100)
        brightness_slider.setMaximum(100)
        brightness_slider.setValue(0)

        contrast_label = QLabel("Contrast")
        contrast_slider = QSlider(Qt.Horizontal)
        contrast_slider.setMinimum(10)
        contrast_slider.setMaximum(300)
        contrast_slider.setValue(100)

        sharpness_label = QLabel("Sharpness")
        sharpness_slider = QSlider(Qt.Horizontal)
        sharpness_slider.setMinimum(0)
        sharpness_slider.setMaximum(100)
        sharpness_slider.setValue(0)

        equalize_label = QLabel("Histogram Equalization")
        equalize_slider = QSlider(Qt.Horizontal)
        equalize_slider.setMinimum(0)
        equalize_slider.setMaximum(1)
        equalize_slider.setValue(0)

        layout.addWidget(brightness_label)
        layout.addWidget(brightness_slider)
        layout.addWidget(contrast_label)
        layout.addWidget(contrast_slider)
        layout.addWidget(sharpness_label)
        layout.addWidget(sharpness_slider)
        layout.addWidget(equalize_label)
        layout.addWidget(equalize_slider)

        def apply_adjustments():
            img = self.original_image_cv.copy()
            brightness = brightness_slider.value()
            contrast = contrast_slider.value() / 100.0
            sharpness = sharpness_slider.value() / 100.0
            equalize = equalize_slider.value() == 1

            adjusted = cv2.convertScaleAbs(img, alpha=contrast, beta=brightness)

            if sharpness > 0:
                blurred = cv2.GaussianBlur(adjusted, (0, 0), 5)
                adjusted = cv2.addWeighted(adjusted, 1 + sharpness, blurred, -sharpness, 0)

            if equalize:
                img_yuv = cv2.cvtColor(adjusted, cv2.COLOR_BGR2YUV)
                img_yuv[:, :, 0] = cv2.equalizeHist(img_yuv[:, :, 0])
                adjusted = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)

            self.current_image_cv = adjusted.copy()
            rgb = cv2.cvtColor(adjusted, cv2.COLOR_BGR2RGB)
            self.image_view.load_cv_array(rgb)

        brightness_slider.valueChanged.connect(apply_adjustments)
        contrast_slider.valueChanged.connect(apply_adjustments)
        sharpness_slider.valueChanged.connect(apply_adjustments)
        equalize_slider.valueChanged.connect(apply_adjustments)

        self.edit_dialog.setLayout(layout)
        self.edit_dialog.show()
