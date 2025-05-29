# pic2vault/gui/main_window.py

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("pic2vault 📸")
        self.setMinimumSize(800, 600)

        # Central widget
        central_widget = QWidget()
        layout = QVBoxLayout()

        # Placeholder UI elements
        label = QLabel("Welcome to pic2vault!")
        label.setStyleSheet("font-size: 24px;")

        layout.addWidget(label)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


def launch_gui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
