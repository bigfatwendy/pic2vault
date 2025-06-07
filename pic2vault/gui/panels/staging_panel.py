# staging_panel.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame
)
from PyQt5.QtCore import QSize, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon, QImage
from PIL import Image
import os
from scanner.scan_interface import scan_to_file

class ScanThread(QThread):
    finished = pyqtSignal(str)

    def run(self):
        result_path = scan_to_file()
        self.finished.emit(result_path if result_path else "")

class StagingPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_staging_dir = "scans/crops"

        # Layouts
        self.staging_layout = QHBoxLayout()
        self.staging_container = QWidget()
        self.staging_container.setLayout(self.staging_layout)

        self.staging_scroll = QScrollArea()
        self.staging_scroll.setWidgetResizable(True)
        self.staging_scroll.setFixedHeight(130)
        self.staging_scroll.setWidget(self.staging_container)
        self.staging_scroll.setFrameShape(QFrame.StyledPanel)

        self.clear_button = QPushButton("🧹 Clear Staging Area")
        self.clear_button.setFixedHeight(30)
        self.clear_button.clicked.connect(self.clear_staging)

        self.swap_button = QPushButton("🔁 Swap Scans/Crops")
        self.swap_button.setFixedHeight(30)
        self.swap_button.clicked.connect(self.swap_staging_directory)

        self.scan_button = QPushButton("📠 Scan")
        self.scan_button.setFixedHeight(30)
        self.scan_button.clicked.connect(self.start_scan)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.swap_button)
        button_layout.addWidget(self.scan_button)

        layout = QVBoxLayout()
        layout.addWidget(self.staging_scroll)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.refresh_staging_area()

    def start_scan(self):
        self.scan_button.setText("📠 Scanning...")
        self.scan_button.setStyleSheet("background-color: orange")
        self.scan_button.setEnabled(False)

        self.scan_thread = ScanThread()
        self.scan_thread.finished.connect(self.finish_scan)
        self.scan_thread.start()

    def finish_scan(self, path):
        self.scan_button.setText("📠 Scan")
        self.scan_button.setStyleSheet("")
        self.scan_button.setEnabled(True)
        if path:
            self.refresh_staging_area()
            self.parent.statusBar().showMessage(f"Scan complete: {os.path.basename(path)}")

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
            placeholder = QPixmap(size[0], size[1])
            placeholder.fill(Qt.gray)
            return placeholder

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

    def clear_staging(self):
        for f in os.listdir(self.current_staging_dir):
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                os.remove(os.path.join(self.current_staging_dir, f))
        self.refresh_staging_area()
        self.parent.statusBar().showMessage("Staging area cleared.")

    def swap_staging_directory(self):
        self.current_staging_dir = "scans/crops" if self.current_staging_dir == "scans" else "scans"
        self.parent.statusBar().showMessage(f"Switched to: {self.current_staging_dir}")
        self.refresh_staging_area()

    def load_staged_image(self, path):
        self.parent.image_display_panel.load_image(path)
        self.parent.current_image_path = path
        self.parent.staged_path = path
        self.parent.statusBar().showMessage(f"Staged image loaded: {os.path.basename(path)}")
