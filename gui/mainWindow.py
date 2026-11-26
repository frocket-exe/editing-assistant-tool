from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QTabWidget
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPalette, QColor
import sys
from .tabs.importTab import ImportTab
from .tabs.silenceTab import SilenceTab
from .tabs.transcribeTab import TranscribeTab


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")
        self.setMinimumSize(QSize(925, 625))

        self.tabs = QTabWidget()
        self.importTab = ImportTab("Import")
        self.silenceTab = SilenceTab("Silences")
        self.transcribeTab = TranscribeTab("Transcribe")
        self.tabs.addTab(self.importTab, self.importTab.title)
        self.tabs.addTab(self.silenceTab, self.silenceTab.title)
        self.tabs.addTab(self.transcribeTab, self.transcribeTab.title)

        self.setCentralWidget(self.tabs)


app = QApplication(sys.argv)

window = MainWindow()
# window = ImportTab("Import")
# window = SilenceTab("Silences")
# window = TranscribeTab("Transcribe")
window.show()

app.exec()