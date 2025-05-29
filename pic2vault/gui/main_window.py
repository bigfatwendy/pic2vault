from PyQt5.QtWidgets import (
    QMainWindow, QLabel, QPushButton, QFileDialog, QVBoxLayout,
    QWidget, QHBoxLayout, QLineEdit, QTextEdit, QListWidget, QListWidgetItem
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize
from PIL import Image
import os
from metadata.metadata_handler import set_exif_data, read_exif_data


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("📸 pic2vault")
        self.setGeometry(100, 100, 1000, 600)

        # ==== LEFT PANEL: Image Gallery ====
        self.gallery = QListWidget()
        self.gallery.setIconSize(QSize(100, 100))
        self.gallery.setFixedWidth(160)
        self.gallery.itemClicked.connect(self.load_from_gallery)

        self.select_folder_btn = QPushButton("Select Folder")
        self.select_folder_btn.clicked.connect(self.choose_folder)

        gallery_layout = QVBoxLayout()
        gallery_layout.addWidget(self.select_folder_btn)
        gallery_layout.addWidget(self.gallery)

        gallery_widget = QWidget()
        gallery_widget.setLayout(gallery_layout)

        # ==== CENTER PANEL: Image Display ====
        self.image_label = QLabel("No image loaded")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid gray;")

        # ==== RIGHT PANEL: Metadata Form ====
        self.meta_title = QLineEdit()
        self.meta_title.setPlaceholderText("Title")

        self.meta_desc = QTextEdit()
        self.meta_desc.setPlaceholderText("Description")

        self.meta_tags = QLineEdit()
        self.meta_tags.setPlaceholderText("Tags (comma-separated)")

        self.meta_date = QLineEdit()
        self.meta_date.setPlaceholderText("Date (YYYY-MM-DD)")

        self.meta_location = QLineEdit()
        self.meta_location.setPlaceholderText("Location (e.g. Paris, France)")


        self.save_button = QPushButton("Save Metadata")
        self.save_button.clicked.connect(self.save_metadata)

        form_layout = QVBoxLayout()
        form_layout.addWidget(self.meta_title)
        form_layout.addWidget(self.meta_desc)
        form_layout.addWidget(self.meta_tags)
        form_layout.addWidget(self.meta_date)
        form_layout.addWidget(self.meta_location)
        form_layout.addWidget(self.save_button)

        form_widget = QWidget()
        form_widget.setLayout(form_layout)

        # ==== Combine Layout ====
        layout = QHBoxLayout()
        layout.addWidget(gallery_widget)
        layout.addWidget(self.image_label, 2)
        layout.addWidget(form_widget, 1)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.statusBar().showMessage("Ready")
        self.current_image_path = None

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if folder:
            self.load_gallery(folder)

    def load_gallery(self, folder_path):
        self.gallery.clear()
        supported_exts = ('.jpg', '.jpeg', '.png')
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(supported_exts):
                full_path = os.path.join(folder_path, filename)
                thumbnail = self.make_thumbnail(full_path)
                item = QListWidgetItem(QIcon(thumbnail), filename)
                item.setData(Qt.UserRole, full_path)
                self.gallery.addItem(item)

    def make_thumbnail(self, path, size=(100, 100)):
        thumb_path = f"{path}.thumb.jpg"
        if not os.path.exists(thumb_path):
            try:
                img = Image.open(path)
                img.thumbnail(size)
                img.save(thumb_path, "JPEG")
            except Exception as e:
                print(f"Error making thumbnail: {e}")
                return path
        return thumb_path

    def load_from_gallery(self, item):
        path = item.data(Qt.UserRole)
        if path:
            pixmap = QPixmap(path)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio))
            self.current_image_path = path
            self.statusBar().showMessage(f"Loaded {os.path.basename(path)}")

    def save_metadata(self):
        title = self.meta_title.text()
        desc = self.meta_desc.toPlainText()
        tags = self.meta_tags.text()
        date = self.meta_date.text()
        location = self.meta_location.text()

        if self.current_image_path:
            print(f"Saving metadata to {self.current_image_path}")
            set_exif_data(self.current_image_path, date_str=date, location_name=location)
            self.statusBar().showMessage("Metadata saved to EXIF.")
        else:
            self.statusBar().showMessage("No image selected.")

