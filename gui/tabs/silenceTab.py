from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QFileDialog, QStackedLayout, QSlider, QLayout
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QBrush
from PySide6.QtCore import QSize, Qt, QRect, QUrl
from scripts.silence import silencesToTimeline, cutsToTimeline, findSilences, createVadVideo
from .tab import Tab
from pathlib import Path
import subprocess
import json
import os


# from PySide6.QtWidgets import QLayout, QWidgetItem

class AspectRatioLayout(QLayout):
    def __init__(self, aspectRatio=16/9, parent=None):
        super().__init__(parent)
        self.aspectRatio = aspectRatio
        self.item = None

    def addItem(self, item):
        self.item = item

    def count(self):
        return 1 if self.item is not None else 0

    def itemAt(self, index):
        if index == 0:
            return self.item
        return None

    def takeAt(self, index):
        if index == 0:
            item = self.item
            self.item = None
            return item
        return None

    def setGeometry(self, rect):
        super().setGeometry(rect)

        if self.item is None:
            return

        width = rect.width()
        height = rect.height()

        # Calculate the largest rectangle that fits
        if width / height > self.aspectRatio:
            width = int(height * self.aspectRatio)
        else:
            height = int(width / self.aspectRatio)

        # Centre the child inside the available space
        x = rect.x() + (rect.width() - width) // 2
        y = rect.y() + (rect.height() - height) // 2

        self.item.setGeometry(QRect(x, y, width, height))

    def sizeHint(self):
        width = 520
        return QSize(width, int(width / self.aspectRatio))

    def minimumSize(self):
        return QSize(0, 0)

    def expandingDirections(self):
        return Qt.Orientation.Horizontal | Qt.Orientation.Vertical


class SilenceTab(Tab):
    def __init__(self, title):
        super().__init__(title)

        self.vadVideo = QVideoWidget()
        self.vadPlayer = QMediaPlayer()
        self.vadPlayer.setVideoOutput(self.vadVideo)
        self.setVadVideo()
        self.vadPlayer.play()

        self.inputVideo = QVideoWidget()
        self.inputAudio = QAudioOutput()
        self.inputPlayer = QMediaPlayer()
        self.inputPlayer.setAudioOutput(self.inputAudio)
        self.inputPlayer.setVideoOutput(self.inputVideo)
        self.setInputVideo()
        self.inputPlayer.playbackStateChanged.connect(self.switchThumbnail)
        self.inputPlayer.play()

        self.thumbnail = QLabel()
        self.generateThumbnail("media/testVideo04.mp4", "gui/thumbnails/inputVideo.jpg")
        self.thumbnailPixmap = (QPixmap("gui/thumbnails/inputVideo.jpg"))
        self.thumbnail.setPixmap(self.thumbnailPixmap.scaled(self.thumbnail.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.thumbnail.setScaledContents(False)
        self.thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail.setStyleSheet("background-color: black;")

        foregroundContainer = QWidget()
        foregroundLayout = QVBoxLayout(foregroundContainer)
        foregroundStackContainer = QWidget()
        foregroundStack = QStackedLayout(foregroundStackContainer)
        foregroundStack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        foregroundLayout.setContentsMargins(10, 10, 10, 10)

        foregroundStack.addWidget(self.inputVideo)
        foregroundStack.addWidget(self.thumbnail)
        foregroundStack.setCurrentWidget(self.thumbnail)
        foregroundLayout.addWidget(foregroundStackContainer)
        vadStackContainer = QWidget()
        vadStack = QStackedLayout(vadStackContainer)
        vadStack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        vadStack.addWidget(self.vadVideo)
        vadStack.addWidget(foregroundContainer)
        vadStack.setCurrentWidget(foregroundContainer)

        vadAspectContainer = QWidget()
        vadAspectContainer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        vadAspectLayout = AspectRatioLayout(4/3, vadAspectContainer)
        vadAspectLayout.addWidget(vadStackContainer)

        inputLabel = QLabel("Input Video: ")
        detectButton = QPushButton("Detect Silence")
        detectButton.clicked.connect(self.detectSilences)
        expEdlButton = QPushButton("Export EDL")

        inputContainer = QWidget()
        inputLayout = QVBoxLayout(inputContainer)
        inputLayout.addWidget(inputLabel)
        inputLayout.addWidget(vadAspectContainer, 1)
        inputLayout.addWidget(detectButton)
        inputLayout.addWidget(expEdlButton)

        attackContainer = QWidget()
        attackLayout = QHBoxLayout(attackContainer)
        attackLabel = QLabel("Attack time:")
        attackSlider = QSlider(Qt.Orientation.Horizontal)
        attackLayout.addWidget(attackLabel)
        attackLayout.addWidget(attackSlider)
        releaseContainer = QWidget()
        releaseLayout = QHBoxLayout(releaseContainer)
        releaseLabel = QLabel("Release time:")
        releaseSlider = QSlider(Qt.Orientation.Horizontal)
        releaseLayout.addWidget(releaseLabel)
        releaseLayout.addWidget(releaseSlider)
        minSilenceContainer = QWidget()
        minSilenceLayout = QHBoxLayout(minSilenceContainer)
        minSilenceLabel = QLabel("Min silence to cut:")
        minSilenceSlider = QSlider(Qt.Orientation.Horizontal)
        minSilenceLayout.addWidget(minSilenceLabel)
        minSilenceLayout.addWidget(minSilenceSlider)
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

        outputContainer = QWidget()
        outputContainer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        outputLayout = AspectRatioLayout(4/3, outputContainer)
        outputLayout.addWidget(self.cutVideo)

        controlsContainer = QWidget()
        controls = QVBoxLayout(controlsContainer)
        controls.addWidget(attackContainer)
        controls.addWidget(releaseContainer)
        controls.addWidget(minSilenceContainer)
        controls.addWidget(cutButton)
        controls.addWidget(outputLabel)
        controls.addWidget(outputContainer)
        controls.addWidget(showVidButton)

        topRowContainer = QWidget()
        topRow = QHBoxLayout(topRowContainer)
        topRow.addWidget(inputContainer)
        topRow.addWidget(controlsContainer)
        topRow.setSpacing(10)

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

        # self.drawTimeline()
        self.drawCuts()

        stylePath = Path(__file__).resolve().parent.parent / "styles" / "silence.qss"
        with open(stylePath, "r") as f:
            self.setStyleSheet(f.read())

    def detectSilences(self):
        findSilences(self.inputVideoPath)
        createVadVideo()
        self.drawTimeline()

    def switchThumbnail(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.thumbnail.hide()
            self.vadVideo.show()
            self.inputVideo.show()
        elif state == QMediaPlayer.PlaybackState.StoppedState:
            self.thumbnail.show()
            self.vadVideo.hide()
            self.inputVideo.hide()

    def generateThumbnail(self, pathIn, pathOut):
        cmd = ["ffmpeg", "-y", "-i", pathIn, "-frames:v", "1", pathOut]
        subprocess.run(cmd)

    def setInputVideo(self):
        with open("json/videoMetrics.json", "r") as f:
            data = json.load(f)
        self.inputVideoPath = data["path"]
        self.inputPlayer.setSource(QUrl.fromLocalFile(self.inputVideoPath))

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