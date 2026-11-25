from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QFileDialog, QStackedLayout, QSlider, QLayout, QMessageBox
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QBrush, QIcon
from PySide6.QtCore import QSize, Qt, QRect, QUrl, QTimer
from scripts.silence import silencesToTimeline, cutsToTimeline, findSilences, createVadVideo, markSilences, removeSilences
from scripts.jsonToEdl import jsonToEdl
from .tab import Tab
from pathlib import Path
import subprocess
import json
import os


# from PySide6.QtWidgets import QLayout, QWidgetItem

def milliToTimecode(mills):
    minutes = int(mills/60000)
    seconds = int(mills/1000) - minutes*60
    return(f"{minutes:02}:{seconds:02}")

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
        self.vadPlayer.mediaStatusChanged.connect(self.vadMediaLoaded)

        self.inputVideo = QVideoWidget()
        self.inputAudio = QAudioOutput()
        self.inputPlayer = QMediaPlayer()
        self.inputPlayer.setAudioOutput(self.inputAudio)
        self.inputPlayer.setVideoOutput(self.inputVideo)
        self.setInputVideo()
        self.inputPlayer.playbackStateChanged.connect(self.switchThumbnail)
        self.inputPlayer.positionChanged.connect(self.updateInputVideoNav)
        # self.inputPlayer.play()

        self.thumbnail = QLabel()
        self.generateThumbnail(self.inputVideoPath, "gui/thumbnails/inputVideo.jpg")
        self.thumbnailPixmap = QPixmap("gui/thumbnails/inputVideo.jpg")
        self.thumbnail.setScaledContents(False)
        self.thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail.setStyleSheet("background-color: black;")

        foregroundContainer = QWidget()
        self.foregroundLayout = QVBoxLayout(foregroundContainer)
        foregroundStackContainer = QWidget()
        foregroundStack = QStackedLayout(foregroundStackContainer)
        foregroundStack.setStackingMode(QStackedLayout.StackingMode.StackAll)
        self.foregroundLayout.setContentsMargins(0, 0, 0, 0)

        foregroundStack.addWidget(self.inputVideo)
        foregroundStack.addWidget(self.thumbnail)
        foregroundStack.setCurrentWidget(self.thumbnail)
        self.foregroundLayout.addWidget(foregroundStackContainer)
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

        navigationContainer = QWidget()
        navigation = QHBoxLayout(navigationContainer)
        playButton = QPushButton()
        playButton.setIcon(QIcon(QPixmap("gui/icons/play.png")))
        playButton.clicked.connect(self.playInput)
        pauseButton = QPushButton()
        pauseButton.setIcon(QIcon(QPixmap("gui/icons/pause.png")))
        pauseButton.clicked.connect(self.pauseInput)
        self.videoProgress = QSlider(Qt.Orientation.Horizontal)
        self.videoProgress.sliderPressed.connect(self.inputSliderPressed)
        self.videoProgress.sliderReleased.connect(self.inputSliderReleased)
        self.videoProgressLabel = QLabel()
        navigation.addWidget(playButton)
        navigation.addWidget(pauseButton)
        navigation.addWidget(self.videoProgress)
        navigation.addWidget(self.videoProgressLabel)

        inputContainer = QWidget()
        inputLayout = QVBoxLayout(inputContainer)
        inputLayout.addWidget(inputLabel)
        inputLayout.addWidget(vadAspectContainer, 1)
        inputLayout.addWidget(navigationContainer)
        inputLayout.addWidget(detectButton)

        attackContainer = QWidget()
        attackLayout = QHBoxLayout(attackContainer)
        attackLabel = QLabel("Attack time:")
        self.attackSlider = QSlider(Qt.Orientation.Horizontal)
        self.attackSlider.setRange(0, 100)
        attackValue = QLabel("0")
        self.attackSlider.valueChanged.connect(lambda: self.changeSliderLabel(self.attackSlider, attackValue))
        attackLayout.addWidget(attackLabel)
        attackLayout.addWidget(self.attackSlider)
        attackLayout.addWidget(attackValue)
        releaseContainer = QWidget()
        releaseLayout = QHBoxLayout(releaseContainer)
        releaseLabel = QLabel("Release time:")
        self.releaseSlider = QSlider(Qt.Orientation.Horizontal)
        self.releaseSlider.setRange(0, 100)
        releaseValue = QLabel("0")
        self.releaseSlider.valueChanged.connect(lambda: self.changeSliderLabel(self.releaseSlider, releaseValue))
        releaseLayout.addWidget(releaseLabel)
        releaseLayout.addWidget(self.releaseSlider)
        releaseLayout.addWidget(releaseValue)
        minSilenceContainer = QWidget()
        minSilenceLayout = QHBoxLayout(minSilenceContainer)
        minSilenceLabel = QLabel("Min silence to cut:")
        self.minSilenceSlider = QSlider(Qt.Orientation.Horizontal)
        self.minSilenceSlider.setRange(0, 500)
        minSilenceValue = QLabel("0")
        self.minSilenceSlider.valueChanged.connect(lambda: self.changeSliderLabel(self.minSilenceSlider, minSilenceValue))
        minSilenceLayout.addWidget(minSilenceLabel)
        minSilenceLayout.addWidget(self.minSilenceSlider)
        minSilenceLayout.addWidget(minSilenceValue)
        self.cutButton = QPushButton("Cut Video")
        self.cutButton.clicked.connect(self.warnNoSilencesDetected)
        self.expEdlButton = QPushButton("Export EDL")
        self.expEdlButton.clicked.connect(self.warnNoCutsMade)
        # self.expEdlButton.clicked.connect(self.exportEdl)

        outputLabel = QLabel("Cut video:")
        self.cutVideo = QVideoWidget()
        self.cutAudio = QAudioOutput()
        self.cutPlayer = QMediaPlayer()
        self.cutPlayer.setAudioOutput(self.cutAudio)
        self.cutPlayer.setVideoOutput(self.cutVideo)
        self.cutPlayer.positionChanged.connect(self.updateCutVideoNav)
        self.cutPlayer.mediaStatusChanged.connect(self.cutMediaLoaded)
        cutNavigationContainer = QWidget()
        cutNavigation = QHBoxLayout(cutNavigationContainer)
        cutPlayButton = QPushButton()
        cutPlayButton.setIcon(QIcon(QPixmap("gui/icons/play.png")))
        cutPlayButton.clicked.connect(self.playCut)
        cutPauseButton = QPushButton()
        cutPauseButton.setIcon(QIcon(QPixmap("gui/icons/pause.png")))
        cutPauseButton.clicked.connect(self.pauseCut)
        self.cutVideoProgress = QSlider(Qt.Orientation.Horizontal)
        self.cutVideoProgress.sliderPressed.connect(self.pauseCut)
        self.cutVideoProgress.sliderReleased.connect(self.cutSliderReleased)
        self.cutVideoProgressLabel = QLabel()
        cutNavigation.addWidget(cutPlayButton)
        cutNavigation.addWidget(cutPauseButton)
        cutNavigation.addWidget(self.cutVideoProgress)
        cutNavigation.addWidget(self.cutVideoProgressLabel)

        outputContainer = QWidget()
        outputContainer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        outputLayout = AspectRatioLayout(4/3, outputContainer)
        outputLayout.addWidget(self.cutVideo)

        controlsContainer = QWidget()
        controls = QVBoxLayout(controlsContainer)
        controls.addWidget(attackContainer)
        controls.addWidget(releaseContainer)
        controls.addWidget(minSilenceContainer)
        controls.addWidget(self.cutButton)
        controls.addWidget(self.expEdlButton)
        controls.addWidget(outputLabel)
        controls.addWidget(outputContainer)
        controls.addWidget(cutNavigationContainer)

        topRowContainer = QWidget()
        topRow = QHBoxLayout(topRowContainer)
        topRow.addWidget(inputContainer)
        topRow.addWidget(controlsContainer)
        topRow.setSpacing(10)

        self.canvasWidth = 850
        self.canvasHeight = 50
        silenceStackContainer = QWidget()
        silenceStack = QStackedLayout(silenceStackContainer)
        self.labelSilences = QLabel()
        self.labelSilences.setAlignment(Qt.AlignmentFlag.AlignCenter)
        canvas = QPixmap(self.canvasWidth, self.canvasHeight)
        canvas.fill(QColor("#11ba2a"))
        self.labelSilences.setPixmap(canvas)
        self.silenceMarker = QLabel()
        self.silenceMarker.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.silenceMarker.setPixmap(QPixmap("gui/icons/timelineMarker.png").scaled(int(self.canvasHeight/2.4), int(self.canvasHeight*1.2)))
        silenceStack.addWidget(self.labelSilences)
        silenceStack.addWidget(self.silenceMarker)
        silenceStack.setCurrentWidget(self.silenceMarker)
        silenceStack.setStackingMode(QStackedLayout.StackingMode.StackAll)

        cutStackContainer = QWidget()
        cutStack = QStackedLayout(cutStackContainer)
        self.labelCuts = QLabel()
        self.labelCuts.setAlignment(Qt.AlignmentFlag.AlignCenter)
        canvasCuts = QPixmap(self.canvasWidth, self.canvasHeight)
        canvasCuts.fill(QColor("#11ba2a"))
        self.labelCuts.setPixmap(canvasCuts)
        self.cutMarker = QLabel()
        self.cutMarker.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cutMarker.setPixmap(QPixmap("gui/icons/timelineMarker.png").scaled(int(self.canvasHeight/2.4), int(self.canvasHeight*1.2)))
        cutStack.addWidget(self.labelCuts)
        cutStack.addWidget(self.cutMarker)
        cutStack.setCurrentWidget(self.cutMarker)
        cutStack.setStackingMode(QStackedLayout.StackingMode.StackAll)

        layout = QVBoxLayout()
        layout.addWidget(topRowContainer)
        layout.addWidget(silenceStackContainer)
        layout.addWidget(cutStackContainer)
        self.setLayout(layout)

        self.switchThumbnail(self.inputPlayer.playbackState())
        QTimer.singleShot(0, self.resizeThumbnail)
        QTimer.singleShot(0, self.setInitalValues)

        stylePath = Path(__file__).resolve().parent.parent / "styles" / "silence.qss"
        with open(stylePath, "r") as f:
            self.setStyleSheet(f.read())

    def cutMediaLoaded(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.cutVideoProgress.setRange(0, self.cutPlayer.duration())
            self.cutVideoProgressLabel.setText(f"00:00/{milliToTimecode(self.cutPlayer.duration())}")
            self.cutPlayer.pause()
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.cutPlayer.pause()

    def updateCutVideoNav(self):
        self.cutVideoProgress.setValue(self.cutPlayer.position())
        self.cutVideoProgressLabel.setText(f"{milliToTimecode(self.cutPlayer.position())}/{milliToTimecode(self.cutPlayer.duration())}")
        timelineCuts = cutsToTimeline()
        print(timelineCuts)
        offset = 0
        percentThrough = (self.cutPlayer.position()/self.inputPlayer.duration())
        for cut in timelineCuts:
            if cut["start"] <= percentThrough+offset:
                offset += cut["size"]
        adjustedPercent = percentThrough + offset
        print(percentThrough)
        print(adjustedPercent)
        self.cutMarker.move(int((adjustedPercent*self.canvasWidth)-self.canvasWidth/2), 0)

    def playCut(self):
        self.cutPlayer.play()

    def pauseCut(self):
        self.cutPlayer.pause()

    def cutSliderReleased(self):
        self.cutPlayer.setPosition(self.cutVideoProgress.value())
        self.cutPlayer.play()

    def warnNoSilencesDetected(self):
        msgBox = QMessageBox()
        msgBox.setText("You have not detected any silences yet.")
        msgBox.exec()

    def warnNoCutsMade(self):
        msgBox = QMessageBox()
        msgBox.setText("You have not created any cuts yet.")
        msgBox.exec()

    def cutVideoFunc(self):
        attack = self.attackSlider.value()/100
        release = self.releaseSlider.value()/100
        minSilence = self.minSilenceSlider.value()/100
        markSilences(minSilence, attack, release)
        self.drawCuts()
        self.expEdlButton.clicked.disconnect()
        self.expEdlButton.clicked.connect(self.exportEdl)
        self.videoOutputPath = QFileDialog.getSaveFileName(self, "Save cut video", "media/cutVideo.mp4", "MP4 (*.mp4)")[0]
        fileExists = (self.videoOutputPath != '')
        if fileExists:
            removeSilences(self.inputVideoPath, self.videoOutputPath)
            self.setCutVideo()

    def changeSliderLabel(self, slider, label):
        label.setText(str(slider.value()/100))

    def setInitalValues(self):
        self.videoProgress.setRange(0, self.inputPlayer.duration())
        self.videoProgressLabel.setText(f"00:00/{milliToTimecode(self.inputPlayer.duration())}")
        self.silenceMarker.move(int(0-(self.canvasWidth/2)), 0)
        self.cutMarker.move(int(0-self.canvasWidth/2), 0)

    def inputSliderPressed(self):
        self.inputPlayer.pause()
        self.vadPlayer.pause()

    def inputSliderReleased(self):
        self.inputPlayer.setPosition(self.videoProgress.value())
        self.vadPlayer.setPosition(self.videoProgress.value())
        self.inputPlayer.play()
        self.vadPlayer.play()

    def updateInputVideoNav(self):
        self.videoProgress.setValue(self.inputPlayer.position())
        self.videoProgressLabel.setText(f"{milliToTimecode(self.inputPlayer.position())}/{milliToTimecode(self.inputPlayer.duration())}")
        self.silenceMarker.move(int(self.inputPlayer.position()/self.inputPlayer.duration()*self.canvasWidth-(self.canvasWidth/2)), 0)

    def playInput(self):
        self.inputPlayer.play()
        self.vadPlayer.play()

    def pauseInput(self):
        self.inputPlayer.pause()
        self.vadPlayer.pause()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resizeThumbnail()

    def resizeThumbnail(self):
        self.thumbnail.setPixmap(self.thumbnailPixmap.scaled(self.thumbnail.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def exportEdl(self):
        fileName = QFileDialog.getSaveFileName(self, "Choose location", "edl/silences.edl", "EDL (*.edl)")[0]
        jsonToEdl("json/silencesToCut.json", fileName)

    def vadMediaLoaded(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.vadPlayer.setPosition(self.inputPlayer.position())
            if self.inputPlayer.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.vadPlayer.play()

    def detectSilences(self):
        findSilences(self.inputVideoPath)
        createVadVideo()
        self.drawTimeline()
        self.setVadVideo()
        self.foregroundLayout.setContentsMargins(10, 10, 10, 10)
        self.silenceMarker.move(int(self.inputPlayer.position()/self.inputPlayer.duration()*self.canvasWidth-(self.canvasWidth/2)), 0)
        self.cutButton.clicked.disconnect()
        self.cutButton.clicked.connect(self.cutVideoFunc)

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
        cutVideoPath = self.videoOutputPath
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
        canvas.fill(QColor("#11ba2a"))
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