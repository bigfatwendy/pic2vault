# image_display_panel.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from gui.widgets.zoomable_image_view import ZoomableImageView

class ImageDisplayPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        self.image_view = ZoomableImageView()
        layout = QVBoxLayout()
        layout.addWidget(self.image_view)
        self.setLayout(layout)

    def load_image(self, path):
        self.image_view.load_cv_image(path, fit_to_view=True)
