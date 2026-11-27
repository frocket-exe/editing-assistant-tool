from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QTabWidget
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPalette, QColor
import sys
from .tabs.importTab import ImportTab
from .tabs.silenceTab import SilenceTab
from .tabs.transcribeTab import TranscribeTab
from .tabs.markWordsTab import MarkWordsTab
from .tabs.analysisTab import AnalysisTab


# Subclass QMainWindow to customize the main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Basic window settings
        self.setWindowTitle("My App")
        self.setMinimumSize(QSize(925, 625))


        self.tabs = QTabWidget()
        # Create Import tab, when a video is imported run initOtherTabs() to add the other tabs
        self.importTab = ImportTab("Import")
        self.importTab.videoImported.connect(self.initOtherTabs)

        self.tabs.addTab(self.importTab, self.importTab.title)
        self.setCentralWidget(self.tabs)

    # Add Silence Tab and Transcribe Tab
    # When silences are detected run initAnalysisTab()
    # When video is transcribed run initMarkWordsTab()
    def initOtherTabs(self, inputVideoPath):
        self.inputVideoPath = inputVideoPath
        self.silenceTab = SilenceTab("Silences")
        self.silenceTab.videoCut.connect(self.initAnalysisTab)
        self.transcribeTab = TranscribeTab("Transcribe")
        self.transcribeTab.videoTranscribed.connect(self.initMarkWordsTab)
        self.tabs.addTab(self.silenceTab, self.silenceTab.title)
        self.tabs.addTab(self.transcribeTab, self.transcribeTab.title)

    # Add Analysis Tab after Silences Tab 
    def initAnalysisTab(self, cutVideoPath):
        self.cutVideoPath = cutVideoPath
        self.analysisTab = AnalysisTab("Analysis", self.inputVideoPath, self.cutVideoPath)
        self.tabs.insertTab(2, self.analysisTab, self.analysisTab.title)

    # Add Mark Words Tab after Transcription Tab
    def initMarkWordsTab(self):
        self.markWordsTab = MarkWordsTab("Mark Words")
        self.tabs.addTab(self.markWordsTab, self.markWordsTab.title)