from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QFileDialog
from PySide6.QtCore import QSize, Qt
from pathlib import Path
import sys
from .tab import Tab
from scripts.getProperties import getProperties
import json

class ImportTab(Tab):
    def __init__(self, title):
        super().__init__(title)