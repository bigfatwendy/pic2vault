# main_window.py
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QScrollArea, QFrame, QHBoxLayout, QSplitter, QSizePolicy
from PyQt5.QtCore import Qt

from gui.panels.gallery_panel import GalleryPanel
from gui.panels.image_display_panel import ImageDisplayPanel
from gui.panels.metadata_panel import MetadataPanel
from gui.panels.staging_panel import StagingPanel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("📸 pic2vault")
        self.setGeometry(100, 100, 1400, 900)

        # === Panels ===
        self.staging_panel = StagingPanel(self)
        self.staging_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.staging_panel.setMaximumHeight(180)

        self.gallery_panel = GalleryPanel(self)
        self.image_display_panel = ImageDisplayPanel(self)
        self.metadata_panel = MetadataPanel(self)

        # ==== Main Split Layout ====
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.gallery_panel)
        splitter.addWidget(self.image_display_panel)
        splitter.addWidget(self.metadata_panel)
        splitter.setSizes([150, 600, 250])

        # ==== Final Main Layout ====
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.staging_panel)
        main_layout.addWidget(splitter)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.statusBar().showMessage("Ready")
