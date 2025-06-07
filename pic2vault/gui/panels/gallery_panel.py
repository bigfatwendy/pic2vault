# gallery_panel.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem
from PyQt5.QtGui import QPixmap, QIcon, QImage
from PyQt5.QtCore import QSize, Qt
from PIL import Image
import os

class GalleryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        self.gallery = QListWidget()
        self.gallery.setIconSize(QSize(100, 100))
        self.gallery.setMinimumWidth(140)
        self.gallery.itemClicked.connect(self.load_from_gallery)

        self.select_folder_btn = QPushButton("Select Folder")
        self.select_folder_btn.clicked.connect(self.choose_folder)

        layout = QVBoxLayout()
        layout.addWidget(self.select_folder_btn)
        layout.addWidget(self.gallery)
        self.setLayout(layout)

    def choose_folder(self):
        from PyQt5.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder:
            self.load_gallery(folder)

    def load_gallery(self, folder_path):
        self.gallery.clear()
        supported_exts = ('.jpg', '.jpeg', '.png')
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(supported_exts):
                full_path = os.path.join(folder_path, filename)
                thumb_pixmap = self.make_thumbnail(full_path)
                item = QListWidgetItem(QIcon(thumb_pixmap), filename)
                item.setData(Qt.UserRole, full_path)
                self.gallery.addItem(item)

    def make_thumbnail(self, path, size=(100, 100)):
        try:
            img = Image.open(path)
            img.thumbnail(size)
            img = img.convert("RGBA")
            data = img.tobytes("raw", "RGBA")
            qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            return QPixmap.fromImage(qimg)
        except Exception as e:
            print(f"Thumbnail error: {e}")
            return QPixmap(path).scaled(size[0], size[1], Qt.KeepAspectRatio)

    def load_from_gallery(self, item):
        path = item.data(Qt.UserRole)
        if path:
            self.parent.image_display_panel.load_image(path)
            self.parent.current_image_path = path
            self.parent.staged_path = None
            self.parent.statusBar().showMessage(f"Loaded {os.path.basename(path)}")
