from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QFileDialog, QSlider
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QBrush, QIcon
from PySide6.QtCore import QSize, Qt, QTimer
from pathlib import Path
import sys
from .tab import Tab, AspectRatioLayout, milliToTimecode
from scripts.transcribe import transcribe, transcriptionToSrt, transcriptToCaptions, sanitise
import json


class TranscribeTab(Tab):
    def __init__(self, title):
        super().__init__(title)

        self.inputPlayer.positionChanged.connect(self.updateInputVideoNav)

        vadAspectContainer = QWidget()
        vadAspectContainer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        vadAspectLayout = AspectRatioLayout(4/3, vadAspectContainer)
        vadAspectLayout.addWidget(self.inputVideo)

        navigationContainer = QWidget()
        navigation = QHBoxLayout(navigationContainer)
        playButton = QPushButton()
        playButton.setIcon(QIcon(QPixmap("gui/icons/play.png")))
        # playButton.clicked.connect(self.playInput)
        pauseButton = QPushButton()
        pauseButton.setIcon(QIcon(QPixmap("gui/icons/pause.png")))
        # pauseButton.clicked.connect(self.pauseInput)
        self.videoProgress = QSlider(Qt.Orientation.Horizontal)
        # self.videoProgress.sliderPressed.connect(self.inputSliderPressed)
        # self.videoProgress.sliderReleased.connect(self.inputSliderReleased)
        self.videoProgressLabel = QLabel()
        navigation.addWidget(playButton)
        navigation.addWidget(pauseButton)
        navigation.addWidget(self.videoProgress)
        navigation.addWidget(self.videoProgressLabel)

        transcribeButton = QPushButton("Transcribe")
        maxWordsContainer = QWidget()
        maxWordsLayout = QHBoxLayout(maxWordsContainer)
        maxWords = QSlider(Qt.Orientation.Horizontal)
        maxWordsLabel = QLabel("0")
        maxWordsLayout.addWidget(maxWords)
        maxWordsLayout.addWidget(maxWordsLabel)
        maxCharactersContainer = QWidget()
        maxCharactersLayout = QHBoxLayout(maxCharactersContainer)
        maxCharacters = QSlider(Qt.Orientation.Horizontal)
        maxCharactersLabel = QLabel("0")
        maxCharactersLayout.addWidget(maxCharacters)
        maxCharactersLayout.addWidget(maxCharactersLabel)
        maxDurationContainer = QWidget()
        maxDurationLayout = QHBoxLayout(maxDurationContainer)
        maxDuration = QSlider(Qt.Orientation.Horizontal)
        maxDurationLabel = QLabel("0")
        maxDurationLayout.addWidget(maxDuration)
        maxDurationLayout.addWidget(maxDurationLabel)
        createSubsButton = QPushButton("Create subtitles")

        westSideContainer = QWidget()
        westSide = QVBoxLayout(westSideContainer)
        westSide.addWidget(vadAspectContainer)
        westSide.addWidget(navigationContainer)
        westSide.addWidget(transcribeButton)
        westSide.addWidget(maxWordsContainer)
        westSide.addWidget(maxCharactersContainer)
        westSide.addWidget(maxDurationContainer)
        westSide.addWidget(createSubsButton)

        eastSideContainer = QWidget()
        eastSide = QVBoxLayout(eastSideContainer)

        layout = QHBoxLayout()
        layout.addWidget(westSideContainer)
        layout.addWidget(eastSideContainer)
        self.setLayout(layout)

        QTimer.singleShot(0, self.setInitialValues)

    def setInitialValues(self):
        self.videoProgressLabel.setText("00:00/00:00")

    def updateInputVideoNav(self):
        pass