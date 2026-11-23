from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QFileDialog, QStackedLayout, QSlider
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QBrush
from PySide6.QtCore import QSize, Qt, QRect, QUrl
from scripts.silence import silencesToTimeline, cutsToTimeline
from .tab import Tab
import json
import os

class SilenceTab(Tab):
    def __init__(self, title):
        super().__init__(title)

        self.vadVideo = QVideoWidget()
        self.vadPlayer = QMediaPlayer()
        self.vadPlayer.setVideoOutput(self.vadVideo)
        self.setVadVideo()
        # self.vadPlayer.play()

        self.inputVideo = QVideoWidget()
        self.inputAudio = QAudioOutput()
        self.inputPlayer = QMediaPlayer()
        self.inputPlayer.setAudioOutput(self.inputAudio)
        self.inputPlayer.setVideoOutput(self.inputVideo)
        self.setInputVideo()
        # self.inputPlayer.play()
        
        vadStackContainer = QWidget()
        vadStack = QStackedLayout(vadStackContainer)
        vadStack.addWidget(self.inputVideo)
        vadStack.addWidget(self.vadVideo)

        inputLabel = QLabel("Input Video: ")
        detectButton = QPushButton("Detect Silence")
        expEdlButton = QPushButton("Export EDL")

        inputContainer = QWidget()
        inputLayout = QVBoxLayout(inputContainer)
        inputLayout.addWidget(inputLabel)
        inputLayout.addWidget(vadStackContainer)
        inputLayout.addWidget(detectButton)
        inputLayout.addWidget(expEdlButton)

        attackLabel = QLabel("Attack time:")
        attackSlider = QSlider(Qt.Orientation.Horizontal)
        releaseLabel = QLabel("Release time:")
        releaseSlider = QSlider(Qt.Orientation.Horizontal)
        minSilenceLabel = QLabel("Min silence to cut:")
        minSilenceSlider = QSlider(Qt.Orientation.Horizontal)
        cutButton = QPushButton("Cut Video")

        outputLabel = QLabel("Cut video:")
        self.cutVideo = QVideoWidget()
        self.cutAudio = QAudioOutput()
        self.cutPlayer = QMediaPlayer()
        self.cutPlayer.setAudioOutput(self.cutAudio)
        self.cutPlayer.setVideoOutput(self.cutVideo)
        self.setCutVideo()
        # self.cutPlayer.play()
        showVidButton = QPushButton("Find video")

        controlsContainer = QWidget()
        controls = QVBoxLayout(controlsContainer)
        controls.addWidget(attackLabel)
        controls.addWidget(attackSlider)
        controls.addWidget(releaseLabel)
        controls.addWidget(releaseSlider)
        controls.addWidget(minSilenceLabel)
        controls.addWidget(minSilenceSlider)
        controls.addWidget(cutButton)
        controls.addWidget(outputLabel)
        controls.addWidget(self.cutVideo)
        controls.addWidget(showVidButton)

        topRowContainer = QWidget()
        topRow = QHBoxLayout(topRowContainer)
        topRow.addWidget(inputContainer)
        topRow.addWidget(controlsContainer)

        self.labelSilences = QLabel()
        self.labelSilences.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.labelCuts = QLabel()
        self.labelCuts.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvasWidth = 850
        self.canvasHeight = 50
        canvas = QPixmap(self.canvasWidth, self.canvasHeight)
        canvas.fill(QColor("#11ba2a"))
        self.labelSilences.setPixmap(canvas)
        canvasCuts = QPixmap(self.canvasWidth, self.canvasHeight)
        canvasCuts.fill(QColor("#11ba2a"))
        self.labelCuts.setPixmap(canvasCuts)

        layout = QVBoxLayout()
        layout.addWidget(topRowContainer)
        layout.addWidget(self.labelSilences)
        layout.addWidget(self.labelCuts)
        self.setLayout(layout)

        self.drawTimeline()
        self.drawCuts()

    def setInputVideo(self):
        with open("json/videoMetrics.json", "r") as f:
            data = json.load(f)
        path = data["path"]
        self.inputPlayer.setSource(QUrl.fromLocalFile(path))

    def setVadVideo(self):
        vadVideoPath = "silent_video_segments/vad.mp4"
        if os.path.exists(vadVideoPath):
            self.vadPlayer.setSource(QUrl.fromLocalFile(vadVideoPath))

    def setCutVideo(self):
        cutVideoPath = "media/cutVideo.mp4"
        if os.path.exists(cutVideoPath):
            self.cutPlayer.setSource(QUrl.fromLocalFile(cutVideoPath))

    def drawTimeline(self):
        timelineSilences = silencesToTimeline()
        canvas = self.labelSilences.pixmap()
        painter = QPainter(canvas)
        pen = QPen()
        pen.setColor(QColor("#d62222"))
        painter.setPen(pen)
        brush = QBrush()
        brush.setColor(QColor("#d62222"))
        brush.setStyle(Qt.SolidPattern)
        painter.setBrush(brush)
        for silence in timelineSilences:
            painter.drawRect(self.canvasWidth*silence["start"], 0, self.canvasWidth*silence["size"], self.canvasHeight)
        painter.end()
        self.labelSilences.setPixmap(canvas)

    def drawCuts(self):
        timelineSilences = silencesToTimeline()
        timelineCuts = cutsToTimeline()
        canvas = self.labelCuts.pixmap()
        painter = QPainter(canvas)
        pen = QPen()
        pen.setColor(QColor("#11ba2a"))
        painter.setPen(pen)
        brush = QBrush()
        brush.setColor(QColor("#eeae36"))
        brush.setStyle(Qt.Dense5Pattern)
        painter.setBrush(brush)
        for silence in timelineSilences:
            painter.drawRect(self.canvasWidth*silence["start"], 0, self.canvasWidth*silence["size"], self.canvasHeight)
        pen.setColor(QColor("#2f5ffc"))
        painter.setPen(pen)
        brush.setColor(QColor("#2f5ffc"))
        brush.setStyle(Qt.SolidPattern)
        painter.setBrush(brush)
        for silence in timelineSilences:
            for cut in timelineCuts:
                if silence["start"] <= cut["start"] and (silence["start"]+silence["size"]) >= (cut["start"]+cut["size"]):
                    painter.drawRect(self.canvasWidth*silence["start"], 0, self.canvasWidth*silence["size"], self.canvasHeight)
        pen.setColor(QColor("#d62222"))
        painter.setPen(pen)
        brush.setColor(QColor("#d62222"))
        painter.setBrush(brush)
        for silence in timelineCuts:
            painter.drawRect(self.canvasWidth*silence["start"], 0, self.canvasWidth*silence["size"], self.canvasHeight)
        painter.end()
        self.labelCuts.setPixmap(canvas)