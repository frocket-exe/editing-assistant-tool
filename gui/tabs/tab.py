from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow
from PySide6.QtCore import QSize, Qt


class Tab(QWidget):
    def __init__(self, title):
        super().__init__()

        self.title = title
        self.setWindowTitle(title)
        self.setMinimumSize(QSize(925, 625))