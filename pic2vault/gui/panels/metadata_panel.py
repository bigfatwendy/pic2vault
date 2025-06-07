# metadata_panel.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QTextEdit, QPushButton
)
from metadata.metadata_handler import set_exif_data
from PyQt5.QtWidgets import QFileDialog
import os

class MetadataPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

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

        layout = QVBoxLayout()
        layout.addWidget(self.meta_title)
        layout.addWidget(self.meta_desc)
        layout.addWidget(self.meta_tags)
        layout.addWidget(self.meta_date)
        layout.addWidget(self.meta_location)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def save_metadata(self):
        if not self.parent.current_image_path:
            self.parent.statusBar().showMessage("No image selected.")
            return

        title = self.meta_title.text()
        desc = self.meta_desc.toPlainText()
        tags = self.meta_tags.text()
        date = self.meta_date.text()
        location = self.meta_location.text()

        set_exif_data(self.parent.current_image_path, date_str=date, location_name=location)

        dest_folder = QFileDialog.getExistingDirectory(self, "Select destination folder")
        if dest_folder:
            filename = os.path.basename(self.parent.current_image_path)
            full_quality_path = os.path.join(dest_folder, filename)
            os.rename(self.parent.current_image_path, full_quality_path)

            if self.parent.staged_path and self.parent.current_image_path == self.parent.staged_path:
                try:
                    os.remove(self.parent.staged_path)
                except:
                    pass
                self.parent.staged_path = None

            self.parent.statusBar().showMessage(f"Saved & moved: {filename}")
            self.parent.current_image_path = None
            self.parent.image_display_panel.load_image(None)
            self.parent.staging_panel.refresh_staging_area()

            self.meta_title.clear()
            self.meta_desc.clear()
            self.meta_tags.clear()
            self.meta_date.clear()
            self.meta_location.clear()
