from PySide6.QtWidgets import (
    QWidget, 
    QPushButton, 
    QLabel, 
    QVBoxLayout, 
    QHBoxLayout, 
    QSizePolicy, 
    QFileDialog, 
    QSlider, 
    QMessageBox,
    QStackedLayout
    )
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QBrush, QIcon
from PySide6.QtCore import Qt, QTimer, QUrl
from .tab import Tab, TagBar, AspectRatioLayout, milliToTimecode
from scripts.markWords import MarkWords, markersToEdl
from scripts.censor import silenceSwears, generateBleep, combineBleep
import json
import os

# Custom Mark Words Tab class inherits from Tab
class MarkWordsTab(Tab):
    def __init__(self, title):
        super().__init__(title)

        # Connect video player to navigation slider
        self.inputPlayer.positionChanged.connect(self.updateInputVideoNav)
        self.setInputVideo()

        # Create container to force video aspect ratio
        inputAspectContainer = QWidget()
        inputAspectContainer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        inputAspectLayout = AspectRatioLayout(4/3, inputAspectContainer)
        inputAspectLayout.addWidget(self.inputVideo)

        # Create navigation container/widgets for main video player
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

        # Creating widgets for playing the censored video
        self.censorVideo = QVideoWidget()
        self.censorAudio = QAudioOutput()
        self.censorPlayer = QMediaPlayer()
        self.censorPlayer.setAudioOutput(self.censorAudio)
        self.censorPlayer.setVideoOutput(self.censorVideo)
        self.censorPlayer.positionChanged.connect(self.updatecensorVideoNav)
        self.censorPlayer.mediaStatusChanged.connect(self.censorMediaLoaded)

        # Use AspectRatioLayout to force video aspect ratio on resize
        censorAspectContainer = QWidget()
        censorAspectContainer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        censorAspectLayout = AspectRatioLayout(4/3, censorAspectContainer)
        censorAspectLayout.addWidget(self.censorVideo)

        # Navigation UI for censor video
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

        # Create "timeline" canvas filled green
        # Add a label with the timelineMarker.png to represent a timeline playhead
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
        markStack.addWidget(self.labelmark)
        markStack.addWidget(self.timelineMarker)
        markStack.setCurrentWidget(self.timelineMarker)
        markStack.setStackingMode(QStackedLayout.StackingMode.StackAll)

        # UI elements relating to user inputting words to censor
        censorContainer = QWidget()
        censorLayout = QVBoxLayout(censorContainer)
        cenLabel = QLabel("Words to censor: ")
        self.censor = TagBar(placeholder="Enter words to censor...", complete=["fuck", "shit"])
        censorLayout.addWidget(cenLabel)
        censorLayout.addWidget(self.censor)

        # UI element relating to user inputting keywords to mark
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

        # Buttons to detect words, silence swear words, censor swear words and export an EDL of markers
        # All connected to their relevant methods
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

        # Add all containers to overarching layout
        layout = QVBoxLayout()
        layout.addWidget(videoPlayersContainer)
        layout.addWidget(markStackContainer)
        layout.addWidget(inputContainer)
        layout.addWidget(buttonsContainer)
        self.setLayout(layout)

        # Calls setInitialValues once UI has been generated
        QTimer.singleShot(0, self.setInitialValues)

    # If swears.json has been created run markersToEdl
    # If not let the user know they need to detect swears first
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


    # If the silenced video has been created, generate a beep and mix it's audio with the silent video to produce a censored video
    # If not, let the user know they need to make a silenced video first
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


    # If swears have been detected create a video where the swear words have been silenced.
    # If not, let the user know they must detect swear words first
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
            

    # Draw yellow rectangles on timeline where keywords are
    # Draw red rectangles on timeline where swear words are
    def markTimeline(self):
        colourKey = {"keyword": "#e8d722", "swear": "#e22323"}
        duration = self.inputPlayer.duration()
        canvas = self.labelmark.pixmap()
        # Fill canvas with green first in case this process is done multiple times, acts as a reset
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


    # Get SRT input file from user, retrieve swear words and keywords to mark and pass these through to MarkWords()
    def detect(self):
        inputFile = QFileDialog.getOpenFileName(self, "Open File", "srt/wordLevelTranscription.srt", f"SRT (*.srt)")[0]
        fileExists = (inputFile != '')
        if fileExists:
            censorWords = list(self.censor.tags)
            keyWordsToDetect = list(self.keyWords.tags)
            self.markers, self.swearMarkers = MarkWords(inputFile, censorWords, keyWordsToDetect)
            self.markTimeline()

    # Play censor video
    def playcensor(self):
        self.censorPlayer.play()

    # Pause censor video
    def pausecensor(self):
        self.censorPlayer.pause()

    # When video progresses, update slider to show progress
    # If silent/censored video has been made, update timeline marker position
    def updatecensorVideoNav(self):
        self.censorVideoProgress.setValue(self.censorPlayer.position())
        self.censorVideoProgressLabel.setText(f"{milliToTimecode(self.censorPlayer.position())}/{milliToTimecode(self.censorPlayer.duration())}")
        if self.videoCensored == True:
            self.timelineMarker.move(int(self.censorPlayer.position()/self.censorPlayer.duration()*self.canvasWidth-(self.canvasWidth/2)), 0)

    # When slider is released, update position in video and play from there
    def censorSliderReleased(self):
        self.censorPlayer.setPosition(self.censorVideoProgress.value())
        self.censorPlayer.play()

    # Set range of slider when censor video has been loaded as this is an asynchronous process
    def censorMediaLoaded(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.censorVideoProgress.setRange(0, self.censorPlayer.duration())
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            # Pausing when the media reaches the end shows the first frame of the video - acting as a thumbnail
            self.censorPlayer.pause()

    # Play the input video
    def playInput(self):
        self.inputPlayer.play()
        self.videoProgress.setRange(0, self.inputPlayer.duration())

    # Pause the input video
    def pauseInput(self):
        self.inputPlayer.pause()

    # Set initial values necessary for logic/styling
    def setInitialValues(self):
        self.videoProgressLabel.setText("00:00/00:00")
        self.censorVideoProgressLabel.setText("00:00/00:00")
        self.timelineMarker.move((int(0-(self.canvasWidth/2))), 0)
        self.videoCensored = False

    # When input video progress changes, set navigation slider value to reflect this
    # If the silenced video and censored video haven't yet been made, update position of timeline marker
    def updateInputVideoNav(self):
        self.videoProgress.setValue(self.inputPlayer.position())
        self.videoProgressLabel.setText(f"{milliToTimecode(self.inputPlayer.position())}/{milliToTimecode(self.inputPlayer.duration())}")
        if self.videoCensored == False:
            self.timelineMarker.move(int(self.inputPlayer.position()/self.inputPlayer.duration()*self.canvasWidth-(self.canvasWidth/2)), 0)

    # When slider is released, update position in video and play from there
    def inputSliderReleased(self):
        self.inputPlayer.setPosition(self.videoProgress.value())
        self.inputPlayer.play()

    # Get value from slider
    def changeSliderLabel(self, slider, label, div=1):
        label.setText(str(slider.value()/div))