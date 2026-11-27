from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QTabWidget
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPalette, QColor
import sys
from .tabs.importTab import ImportTab
from .tabs.silenceTab import SilenceTab
from .tabs.transcribeTab import TranscribeTab
from .tabs.markWordsTab import MarkWordsTab
from .tabs.analysisTab import AnalysisTab


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")
        self.setMinimumSize(QSize(925, 625))


        self.tabs = QTabWidget()
        self.importTab = ImportTab("Import")
        self.importTab.videoImported.connect(self.initOtherTabs)
        self.tabs.addTab(self.importTab, self.importTab.title)

        self.setCentralWidget(self.tabs)

    def initOtherTabs(self, inputVideoPath):
        self.inputVideoPath = inputVideoPath
        self.silenceTab = SilenceTab("Silences")
        self.silenceTab.videoCut.connect(self.initAnalysisTab)
        self.transcribeTab = TranscribeTab("Transcribe")
        self.transcribeTab.videoTranscribed.connect(self.initMarkWordsTab)
        self.tabs.addTab(self.silenceTab, self.silenceTab.title)
        self.tabs.addTab(self.transcribeTab, self.transcribeTab.title)

    def initAnalysisTab(self, cutVideoPath):
        self.cutVideoPath = cutVideoPath
        self.analysisTab = AnalysisTab("Analysis", self.inputVideoPath, self.cutVideoPath)
        self.tabs.insertTab(2, self.analysisTab, self.analysisTab.title)

    def initMarkWordsTab(self):
        self.markWordsTab = MarkWordsTab("Mark Words")
        self.tabs.addTab(self.markWordsTab, self.markWordsTab.title)


# app = QApplication(sys.argv)

# window = MainWindow()
# window.show()

# app.exec()