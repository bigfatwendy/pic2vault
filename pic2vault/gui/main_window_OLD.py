from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QFileDialog, QVBoxLayout,
    QWidget, QHBoxLayout, QLineEdit, QTextEdit, QListWidget, QListWidgetItem,
    QScrollArea, QFrame, QSplitter
)
from PyQt5.QtGui import QPixmap, QIcon, QImage
from PyQt5.QtCore import Qt, QSize
from PIL import Image
import os
import cv2

from metadata.metadata_handler import set_exif_data, read_exif_data
from scanner.scan_interface import scan_to_file
from gui.widgets.zoomable_image_view import ZoomableImageView

Image.MAX_IMAGE_PIXELS = None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("\ud83d\udcf8 pic2vault")
        self.setGeometry(100, 100, 1000, 600)

        self.current_staging_dir = "scans"

        # === Staging Area ===
        self.staging_layout = QHBoxLayout()
        self.staging_container = QWidget()
        self.staging_container.setLayout(self.staging_layout)

        self.staging_scroll = QScrollArea()
        self.staging_scroll.setWidgetResizable(True)
        self.staging_scroll.setFixedHeight(130)
        self.staging_scroll.setWidget(self.staging_container)
        self.staging_scroll.setFrameShape(QFrame.StyledPanel)

        self.clear_staging_btn = QPushButton("\ud83e\uddd9\u200d\u2640\ufe0f Clear Staging Area")
        self.clear_staging_btn.clicked.connect(self.clear_staging)

        self.swap_staging_btn = QPushButton("\ud83d\udd01 Swap Scans/Crops")
        self.swap_staging_btn.clicked.connect(self.swap_staging_directory)

        staging_btn_layout = QHBoxLayout()
        staging_btn_layout.addWidget(self.clear_staging_btn)
        staging_btn_layout.addWidget(self.swap_staging_btn)

        staging_btn_container = QWidget()
        staging_btn_container.setLayout(staging_btn_layout)

        # ==== LEFT PANEL: Image Gallery ====
        self.gallery = QListWidget()
        self.gallery.setIconSize(QSize(100, 100))
        self.gallery.setMinimumWidth(140)
        self.gallery.itemClicked.connect(self.load_from_gallery)

        self.select_folder_btn = QPushButton("Select Folder")
        self.select_folder_btn.clicked.connect(self.choose_folder)

        gallery_layout = QVBoxLayout()
        gallery_layout.addWidget(self.select_folder_btn)
        gallery_layout.addWidget(self.gallery)

        gallery_widget = QWidget()
        gallery_widget.setLayout(gallery_layout)

        # ==== CENTER PANEL: Image Display ====
        self.image_label = ZoomableImageView()

        image_preview_container = QWidget()
        image_layout = QVBoxLayout()
        image_layout.addWidget(self.image_label)
        image_preview_container.setLayout(image_layout)

        # ==== RIGHT PANEL: Metadata Form ====
        self.scan_button = QPushButton("\ud83d\udcf0 Scan Photo")
        self.scan_button.clicked.connect(self.scan_and_load)

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
        form_layout.addWidget(self.scan_button)
        form_layout.addWidget(self.meta_title)
        form_layout.addWidget(self.meta_desc)
        form_layout.addWidget(self.meta_tags)
        form_layout.addWidget(self.meta_date)
        form_layout.addWidget(self.meta_location)
        form_layout.addWidget(self.save_button)

        form_widget = QWidget()
        form_widget.setLayout(form_layout)

        # ==== Main Split Layout ====
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(gallery_widget)
        splitter.addWidget(image_preview_container)
        splitter.addWidget(form_widget)
        splitter.setSizes([150, 600, 250])

        # ==== Final Main Layout ====
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.staging_scroll)
        main_layout.addWidget(staging_btn_container)
        main_layout.addWidget(splitter)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # === State ===
        self.statusBar().showMessage("Ready")
        self.current_image_path = None
        self.staged_path = None

        self.refresh_staging_area()

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
            self.image_label.load_cv_image(path, fit_to_view=False)
            self.current_image_path = path
            self.staged_path = None
            self.statusBar().showMessage(f"Loaded {os.path.basename(path)}")

    def save_metadata(self):
        if not self.current_image_path:
            self.statusBar().showMessage("No image selected.")
            return

        title = self.meta_title.text()
        desc = self.meta_desc.toPlainText()
        tags = self.meta_tags.text()
        date = self.meta_date.text()
        location = self.meta_location.text()

        set_exif_data(self.current_image_path, date_str=date, location_name=location)

        dest_folder = QFileDialog.getExistingDirectory(self, "Select destination folder")
        if dest_folder:
            filename = os.path.basename(self.current_image_path)
            full_quality_path = os.path.join(dest_folder, filename)
            os.rename(self.current_image_path, full_quality_path)

            if self.staged_path and self.current_image_path == self.staged_path:
                try:
                    os.remove(self.staged_path)
                except:
                    pass
                self.staged_path = None

            self.statusBar().showMessage(f"Saved & moved: {filename}")
            self.current_image_path = None
            self.image_label.load_cv_image(None)
            self.refresh_staging_area()

            self.meta_title.clear()
            self.meta_desc.clear()
            self.meta_tags.clear()
            self.meta_date.clear()
            self.meta_location.clear()

    def scan_and_load(self):
        path = scan_to_file()
        if path:
            self.image_label.load_cv_image(path, fit_to_view=False)
            self.current_image_path = path
            self.staged_path = path
            self.statusBar().showMessage(f"Scanned image loaded: {os.path.basename(path)}")
            self.refresh_staging_area()

    def refresh_staging_area(self):
        for i in reversed(range(self.staging_layout.count())):
            widget = self.staging_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        os.makedirs(self.current_staging_dir, exist_ok=True)
        supported_exts = ('.jpg', '.jpeg', '.png')
        for filename in os.listdir(self.current_staging_dir):
            if filename.lower().endswith(supported_exts):
                path = os.path.join(self.current_staging_dir, filename)
                thumb_pixmap = self.make_thumbnail(path)
                btn = QPushButton()
                btn.setIcon(QIcon(thumb_pixmap))
                btn.setIconSize(QSize(100, 100))
                btn.setFixedSize(110, 110)
                btn.setToolTip(filename)
                btn.clicked.connect(lambda checked, p=path: self.load_staged_image(p))
                self.staging_layout.addWidget(btn)

    def load_staged_image(self, path):
        self.image_label.load_cv_image(path, fit_to_view=False)
        self.current_image_path = path
        self.staged_path = path
        self.statusBar().showMessage(f"Staged image loaded: {os.path.basename(path)}")

    def clear_staging(self):
        for f in os.listdir(self.current_staging_dir):
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                os.remove(os.path.join(self.current_staging_dir, f))
        self.refresh_staging_area()
        self.statusBar().showMessage("Staging area cleared.")

    def swap_staging_directory(self):
        self.current_staging_dir = "scans/crops" if self.current_staging_dir == "scans" else "scans"
        self.statusBar().showMessage(f"Switched to: {self.current_staging_dir}")
        self.refresh_staging_area()
