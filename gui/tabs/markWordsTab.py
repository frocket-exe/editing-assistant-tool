from PySide6.QtWidgets import (
    QApplication, 
    QWidget, 
    QPushButton, 
    QMainWindow, 
    QGridLayout, 
    QLabel, 
    QVBoxLayout, 
    QHBoxLayout, 
    QSizePolicy, 
    QFileDialog, 
    QSlider, 
    QComboBox, 
    QLineEdit, 
    QCompleter, 
    QListWidget, 
    QListWidgetItem, 
    QListView,
    QFrame,
    QToolButton,
    QCheckBox,
    QMessageBox,
    QStackedLayout
    )
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QBrush, QIcon
from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot, QUrl
from pathlib import Path
import sys
from .tab import Tab, TagBar, AspectRatioLayout, milliToTimecode
from scripts.markWords import MarkWords, markersToEdl
from scripts.censor import silenceSwears, generateBleep, combineBleep
import json
import os

class MarkWordsTab(Tab):
    def __init__(self, title):
        super().__init__(title)

        self.inputPlayer.positionChanged.connect(self.updateInputVideoNav)
        self.setInputVideo()

        inputAspectContainer = QWidget()
        inputAspectContainer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        inputAspectLayout = AspectRatioLayout(4/3, inputAspectContainer)
        inputAspectLayout.addWidget(self.inputVideo)

        navigationContainer = QWidget()
        navigation = QHBoxLayout(navigationContainer)
        playButton = QPushButton()
        playButton.setIcon(QIcon(QPixmap("gui/icons/play.png")))
        playButton.clicked.connect(self.playInput)
        pauseButton = QPushButton()
        pauseButton.setIcon(QIcon(QPixmap("gui/icons/pause.png")))
        pauseButton.clicked.connect(self.pauseInput)
        self.videoProgress = QSlider(Qt.Orientation.Horizontal)
        self.videoProgress.sliderPressed.connect(self.pauseInput)
        self.videoProgress.sliderReleased.connect(self.inputSliderReleased)
        self.videoProgressLabel = QLabel()
        navigation.addWidget(playButton)
        navigation.addWidget(pauseButton)
        navigation.addWidget(self.videoProgress)
        navigation.addWidget(self.videoProgressLabel)

        mainVideoContainer = QWidget()
        mainVideo = QVBoxLayout(mainVideoContainer)
        mainVideo.addWidget(inputAspectContainer)
        mainVideo.addWidget(navigationContainer)

        self.censorVideo = QVideoWidget()
        self.censorAudio = QAudioOutput()
        self.censorPlayer = QMediaPlayer()
        self.censorPlayer.setAudioOutput(self.censorAudio)
        self.censorPlayer.setVideoOutput(self.censorVideo)
        self.censorPlayer.positionChanged.connect(self.updatecensorVideoNav)
        self.censorPlayer.mediaStatusChanged.connect(self.censorMediaLoaded)
        
        censorAspectContainer = QWidget()
        censorAspectContainer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        censorAspectLayout = AspectRatioLayout(4/3, censorAspectContainer)
        censorAspectLayout.addWidget(self.censorVideo)

        censorNavigationContainer = QWidget()
        censorNavigation = QHBoxLayout(censorNavigationContainer)
        censorPlayButton = QPushButton()
        censorPlayButton.setIcon(QIcon(QPixmap("gui/icons/play.png")))
        censorPlayButton.clicked.connect(self.playcensor)
        censorPauseButton = QPushButton()
        censorPauseButton.setIcon(QIcon(QPixmap("gui/icons/pause.png")))
        censorPauseButton.clicked.connect(self.pausecensor)
        self.censorVideoProgress = QSlider(Qt.Orientation.Horizontal)
        self.censorVideoProgress.sliderPressed.connect(self.pausecensor)
        self.censorVideoProgress.sliderReleased.connect(self.censorSliderReleased)
        self.censorVideoProgressLabel = QLabel()
        censorNavigation.addWidget(censorPlayButton)
        censorNavigation.addWidget(censorPauseButton)
        censorNavigation.addWidget(self.censorVideoProgress)
        censorNavigation.addWidget(self.censorVideoProgressLabel)

        censorVideoContainer = QWidget()
        censorVideo = QVBoxLayout(censorVideoContainer)
        censorVideo.addWidget(censorAspectContainer)
        censorVideo.addWidget(censorNavigationContainer)

        videoPlayersContainer = QWidget()
        videoPlayers = QHBoxLayout(videoPlayersContainer)
        videoPlayers.addWidget(mainVideoContainer)
        videoPlayers.addWidget(censorVideoContainer)

        self.canvasWidth = 850
        self.canvasHeight = 50
        markStackContainer = QWidget()
        markStack = QStackedLayout(markStackContainer)
        self.labelmark = QLabel()
        self.labelmark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        canvas = QPixmap(self.canvasWidth, self.canvasHeight)
        canvas.fill(QColor("#11ba2a"))
        self.labelmark.setPixmap(canvas)
        self.timelineMarker = QLabel()
        self.timelineMarker.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timelineMarker.setPixmap(QPixmap("gui/icons/timelineMarker.png").scaled(int(self.canvasHeight/2.4), int(self.canvasHeight*1.2)))
        print(f"{int(0-(self.canvasWidth/2))}\n\n\n\n\n\n\n\n\n")
        markStack.addWidget(self.labelmark)
        markStack.addWidget(self.timelineMarker)
        markStack.setCurrentWidget(self.timelineMarker)
        markStack.setStackingMode(QStackedLayout.StackingMode.StackAll)

        censorContainer = QWidget()
        censorLayout = QVBoxLayout(censorContainer)
        cenLabel = QLabel("Words to censor: ")
        self.censor = TagBar(placeholder="Enter words to censor...", complete=["fuck", "shit"])
        censorLayout.addWidget(cenLabel)
        censorLayout.addWidget(self.censor)

        keyContainer = QWidget()
        keyLayout = QVBoxLayout(keyContainer)
        keyLabel = QLabel("Keywords to detect: ")
        self.keyWords = TagBar(placeholder="Enter keywords to mark...")
        keyLayout.addWidget(keyLabel)
        keyLayout.addWidget(self.keyWords)
        
        inputContainer = QWidget()
        inputLayout = QHBoxLayout(inputContainer)
        inputLayout.addWidget(censorContainer)
        inputLayout.addWidget(keyContainer)

        detectButt = QPushButton("Detect")
        detectButt.clicked.connect(self.detect)
        silenceButt = QPushButton("Silence swears")
        silenceButt.clicked.connect(self.silenceSwearsButt)
        censorButt = QPushButton("Censor swears")
        censorButt.clicked.connect(self.censorSwearsButt)
        downloadButt = QPushButton("Export EDL")
        downloadButt.clicked.connect(self.exportEdl)

        buttonsContainer = QWidget()
        buttonsLayout = QHBoxLayout(buttonsContainer)
        buttonsLayout.addWidget(detectButt)
        buttonsLayout.addWidget(silenceButt)
        buttonsLayout.addWidget(censorButt)
        buttonsLayout.addWidget(downloadButt)

        layout = QVBoxLayout()
        layout.addWidget(videoPlayersContainer)
        layout.addWidget(markStackContainer)
        layout.addWidget(inputContainer)
        layout.addWidget(buttonsContainer)
        self.setLayout(layout)
        QTimer.singleShot(0, self.setInitialValues)

    def exportEdl(self):
        if os.path.exists("json/swears.json"):
            with open("json/videoMetrics.json", "r") as f:
                metadata = json.load(f)
            frameRate = int(metadata["video"]["r_frame_rate"][:-2])
            self.edlFilePath = QFileDialog.getSaveFileName(self, "Save EDL", "edl/markers.edl", "EDL (*.edl)")[0]
            markersToEdl(self.swearMarkers, self.edlFilePath, frameRate)
        else:
            msgBox = QMessageBox()
            msgBox.setText("You have not detected any swears yet.")
            msgBox.exec()


    def censorSwearsButt(self):
        if self.videoCensored == True:
            self.censoredVideoPath = QFileDialog.getSaveFileName(self, "Save censored video", "censor/censoredVideo.mp4", "MP4 (*.mp4)")[0]
            generateBleep((self.censorPlayer.duration()/1000))
            combineBleep(self.silentVideoPath, self.censoredVideoPath)
            self.censorPlayer.setSource(QUrl.fromLocalFile(self.censoredVideoPath))
            self.censorPlayer.pause()
        else:
            msgBox = QMessageBox()
            msgBox.setText("You must detect swears and make a silenced video first.")
            msgBox.exec()


    def silenceSwearsButt(self):
        if os.path.exists("json/swears.json"):
            self.silentVideoPath = QFileDialog.getSaveFileName(self, "Save silenced video", "censor/silencedVideo.mp4", "MP4 (*.mp4)")[0]
            silenceSwears(self.inputVideoPath, self.silentVideoPath)
            self.censorPlayer.setSource(QUrl.fromLocalFile(self.silentVideoPath))
            self.videoCensored = True
            self.censorPlayer.pause()
        else:
            msgBox = QMessageBox()
            msgBox.setText("You have not detected any swears yet.")
            msgBox.exec()
            

    def markTimeline(self):
        colourKey = {"keyword": "#e8d722", "swear": "#e22323"}
        duration = self.inputPlayer.duration()
        canvas = self.labelmark.pixmap()
        canvas.fill(QColor("#11ba2a"))
        painter = QPainter(canvas)
        pen = QPen()
        brush = QBrush()
        brush.setStyle(Qt.SolidPattern)
        for marker in self.markers:
            start = (marker["timeIn"]*1000)/duration
            size = (marker["duration"]*1000)/duration
            colour = colourKey.get(marker["type"])
            pen.setColor(QColor(colour))
            painter.setPen(pen)
            brush.setColor(QColor(colour))
            painter.setBrush(brush)
            painter.drawRect(self.canvasWidth*start, 0, self.canvasWidth*size, self.canvasHeight)
        painter.end()
        self.labelmark.setPixmap(canvas)


    def detect(self):
        inputFile = QFileDialog.getOpenFileName(self, "Open File", "srt/wordLevelTranscription.srt", f"SRT (*.srt)")[0]
        fileExists = (inputFile != '')
        if fileExists:
            censorWords = list(self.censor.tags)
            keyWordsToDetect = list(self.keyWords.tags)
            self.markers, self.swearMarkers = MarkWords(inputFile, censorWords, keyWordsToDetect)
            self.markTimeline()

    def playcensor(self):
        self.censorPlayer.play()

    def pausecensor(self):
        self.censorPlayer.pause()

    def updatecensorVideoNav(self):
        self.censorVideoProgress.setValue(self.censorPlayer.position())
        self.censorVideoProgressLabel.setText(f"{milliToTimecode(self.censorPlayer.position())}/{milliToTimecode(self.censorPlayer.duration())}")
        if self.videoCensored == True:
            self.timelineMarker.move(int(self.censorPlayer.position()/self.censorPlayer.duration()*self.canvasWidth-(self.canvasWidth/2)), 0)

    def censorSliderReleased(self):
        self.censorPlayer.setPosition(self.censorVideoProgress.value())
        self.censorPlayer.play()

    def censorMediaLoaded(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.censorVideoProgress.setRange(0, self.censorPlayer.duration())
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.censorPlayer.pause()

    def playInput(self):
        self.inputPlayer.play()
        self.videoProgress.setRange(0, self.inputPlayer.duration())

    def pauseInput(self):
        self.inputPlayer.pause()

    def setInitialValues(self):
        self.videoProgressLabel.setText("00:00/00:00")
        self.censorVideoProgressLabel.setText("00:00/00:00")
        self.timelineMarker.move((int(0-(self.canvasWidth/2))), 0)
        self.videoCensored = False

    def updateInputVideoNav(self):
        self.videoProgress.setValue(self.inputPlayer.position())
        self.videoProgressLabel.setText(f"{milliToTimecode(self.inputPlayer.position())}/{milliToTimecode(self.inputPlayer.duration())}")
        if self.videoCensored == False:
            self.timelineMarker.move(int(self.inputPlayer.position()/self.inputPlayer.duration()*self.canvasWidth-(self.canvasWidth/2)), 0)

    def inputSliderReleased(self):
        self.inputPlayer.setPosition(self.videoProgress.value())
        self.inputPlayer.play()

    def changeSliderLabel(self, slider, label, div=1):
        label.setText(str(slider.value()/div))