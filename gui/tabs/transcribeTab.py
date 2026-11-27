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
    QMessageBox
    )
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QBrush, QIcon
from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot, QUrl, Signal
from pathlib import Path
import sys
from .tab import Tab, AspectRatioLayout, milliToTimecode, TagBar
from scripts.transcribe import transcribe, transcriptionToSrt, transcriptToCaptions, sanitise
import json
import subprocess
import os



class TranscribeTab(Tab):
    videoTranscribed = Signal()
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

        transcribeButton = QPushButton("Transcribe")
        transcribeButton.clicked.connect(self.transcribeButtonFunction)
        self.maxWordsTitle = QLabel("Max words per caption:")
        self.maxWordsContainer = QWidget()
        self.maxWordsLayout = QHBoxLayout(self.maxWordsContainer)
        self.maxWords = QSlider(Qt.Orientation.Horizontal)
        self.maxWords.setRange(1, 12)
        self.maxWordsLabel = QLabel("1")
        self.maxWords.valueChanged.connect(lambda: self.changeSliderLabel(self.maxWords, self.maxWordsLabel))
        self.maxWordsLayout.addWidget(self.maxWords)
        self.maxWordsLayout.addWidget(self.maxWordsLabel)
        self.maxCharactersTitle = QLabel("Max characters per caption:")
        self.maxCharactersContainer = QWidget()
        self.maxCharactersLayout = QHBoxLayout(self.maxCharactersContainer)
        self.maxCharacters = QSlider(Qt.Orientation.Horizontal)
        self.maxCharacters.setRange(1, 50)
        self.maxCharactersLabel = QLabel("1")
        self.maxCharacters.valueChanged.connect(lambda: self.changeSliderLabel(self.maxCharacters, self.maxCharactersLabel))
        self.maxCharactersLayout.addWidget(self.maxCharacters)
        self.maxCharactersLayout.addWidget(self.maxCharactersLabel)
        self.maxDurationTitle = QLabel("Max duration of each caption (s):")
        self.maxDurationContainer = QWidget()
        self.maxDurationLayout = QHBoxLayout(self.maxDurationContainer)
        self.maxDuration = QSlider(Qt.Orientation.Horizontal)
        self.maxDuration.setRange(1, 100)
        self.maxDurationLabel = QLabel("0.1")
        self.maxDuration.valueChanged.connect(lambda: self.changeSliderLabel(self.maxDuration, self.maxDurationLabel, 10))
        self.maxDurationLayout.addWidget(self.maxDuration)
        self.maxDurationLayout.addWidget(self.maxDurationLabel)
        fillGapsContainer = QWidget()
        fillGapsLayout = QHBoxLayout(fillGapsContainer)
        fillGapsLabel = QLabel("Fill gaps between subtitles ")
        self.fillGaps = QCheckBox()
        fillGapsLayout.addWidget(fillGapsLabel)
        fillGapsLayout.addWidget(self.fillGaps)
        fillGapsLayout.addStretch()
        createSubsButton = QPushButton("Create subtitles")
        createSubsButton.clicked.connect(self.generateCaptions)

        westSideContainer = QWidget()
        westSide = QVBoxLayout(westSideContainer)
        westSide.addWidget(inputAspectContainer)
        westSide.addWidget(navigationContainer)
        westSide.addWidget(transcribeButton)
        westSide.addWidget(self.maxWordsTitle)
        westSide.addWidget(self.maxWordsContainer)
        westSide.addWidget(self.maxCharactersTitle)
        westSide.addWidget(self.maxCharactersContainer)
        westSide.addWidget(self.maxDurationTitle)
        westSide.addWidget(self.maxDurationContainer)
        westSide.addWidget(fillGapsContainer)
        westSide.addWidget(createSubsButton)

        self.subVideo = QVideoWidget()
        self.subAudio = QAudioOutput()
        self.subPlayer = QMediaPlayer()
        self.subPlayer.setAudioOutput(self.subAudio)
        self.subPlayer.setVideoOutput(self.subVideo)
        self.subPlayer.positionChanged.connect(self.updateSubVideoNav)
        self.subPlayer.mediaStatusChanged.connect(self.subMediaLoaded)
        
        subAspectContainer = QWidget()
        subAspectContainer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        subAspectLayout = AspectRatioLayout(4/3, subAspectContainer)
        subAspectLayout.addWidget(self.subVideo)

        subNavigationContainer = QWidget()
        subNavigation = QHBoxLayout(subNavigationContainer)
        subPlayButton = QPushButton()
        subPlayButton.setIcon(QIcon(QPixmap("gui/icons/play.png")))
        subPlayButton.clicked.connect(self.playSub)
        subPauseButton = QPushButton()
        subPauseButton.setIcon(QIcon(QPixmap("gui/icons/pause.png")))
        subPauseButton.clicked.connect(self.pauseSub)
        self.subVideoProgress = QSlider(Qt.Orientation.Horizontal)
        self.subVideoProgress.sliderPressed.connect(self.pauseSub)
        self.subVideoProgress.sliderReleased.connect(self.subSliderReleased)
        self.subVideoProgressLabel = QLabel()
        subNavigation.addWidget(subPlayButton)
        subNavigation.addWidget(subPauseButton)
        subNavigation.addWidget(self.subVideoProgress)
        subNavigation.addWidget(self.subVideoProgressLabel)

        sanLabel = QLabel("Sanitisation:")
        caseLabel = QLabel("Case conversion:")
        self.caseConv = QComboBox()
        self.caseConv.addItems(["None", "UPPERCASE", "lowercase"])
        keepCapLabel = QLabel("Words to keep capital: ")
        self.keepCap = TagBar(placeholder="Enter words to keep capitalised...", complete=["I", "I'm", "I've", "I'd", "I'll"])
        puncLabel = QLabel("Punctuation to remove: ")
        self.puncList = QListWidget()
        self.puncList.setFlow(QListView.Flow.LeftToRight)
        self.puncList.setWrapping(True)
        self.puncList.setResizeMode(QListView.ResizeMode.Adjust)
        defActive = ['.', '!', '"', ',', ';']
        for punc in ['.', '!', '"', ',', ';', ':', '-', "?"]:
            listItem = QListWidgetItem(punc)
            listItem.setFlags(listItem.flags() | Qt.ItemIsUserCheckable)
            if punc in defActive:
                listItem.setCheckState(Qt.Checked)
            else:
                listItem.setCheckState(Qt.Unchecked)
            self.puncList.addItem(listItem)
        cenLabel = QLabel("Words to censor: ")
        self.censor = TagBar(placeholder="Enter words to censor...", complete=["fuck", "shit"])
        sanitiseButton = QPushButton("Sanitise captions")
        sanitiseButton.clicked.connect(self.sanitiseCaptions)
        burnButton = QPushButton("Add subtitles to video")
        burnButton.clicked.connect(self.burnCaptions)


        eastSideContainer = QWidget()
        eastSide = QVBoxLayout(eastSideContainer)
        eastSide.addWidget(subAspectContainer)
        eastSide.addWidget(subNavigationContainer)
        eastSide.addWidget(sanLabel)
        eastSide.addWidget(caseLabel)
        eastSide.addWidget(self.caseConv)
        eastSide.addWidget(keepCapLabel)
        eastSide.addWidget(self.keepCap)
        eastSide.addWidget(puncLabel)
        eastSide.addWidget(self.puncList)
        eastSide.addWidget(cenLabel)
        eastSide.addWidget(self.censor)
        eastSide.addWidget(sanitiseButton)
        eastSide.addWidget(burnButton)

        layout = QHBoxLayout()
        layout.addWidget(westSideContainer)
        layout.addWidget(eastSideContainer)
        self.setLayout(layout)

        QTimer.singleShot(0, self.setInitialValues)

    def playSub(self):
        self.subPlayer.play()

    def pauseSub(self):
        self.subPlayer.pause()

    def updateSubVideoNav(self):
        self.subVideoProgress.setValue(self.subPlayer.position())
        self.subVideoProgressLabel.setText(f"{milliToTimecode(self.subPlayer.position())}/{milliToTimecode(self.subPlayer.duration())}")

    def subSliderReleased(self):
        self.subPlayer.setPosition(self.subVideoProgress.value())
        self.subPlayer.play()

    def burnCaptions(self):
        inputFile = QFileDialog.getOpenFileName(self, "Open File", "srt/sanitised.srt", f"SRT (*.srt)")[0]
        subtitlePath = os.path.abspath(inputFile).replace("\\", "/")
        subtitlePath = subtitlePath.replace(":", r"\:")
        subtitlePath = subtitlePath.replace("'", r"\'")
        self.subVideoPath = QFileDialog.getSaveFileName(self, "Choose location", "media/subtitledVid.mp4", "MP4 (*.mp4)")[0]
        cmd = ["ffmpeg", "-y", "-i", self.inputVideoPath, "-vf", f"subtitles='{subtitlePath}'", self.subVideoPath]
        subprocess.run(cmd)
        self.subPlayer.setSource(QUrl.fromLocalFile(self.subVideoPath))
        self.subPlayer.pause()
        self.subVideoProgress.setRange(0, self.subPlayer.duration())

    def subMediaLoaded(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.subVideoProgress.setRange(0, self.subPlayer.duration())
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.subPlayer.pause()

    def sanitiseCaptions(self):
        inputFile = QFileDialog.getOpenFileName(self, "Open File", "srt/", f"SRT (*.srt)")[0]
        fileExists = (inputFile != '')
        if fileExists:
            outputFile = QFileDialog.getSaveFileName(self, "Choose location", "srt/sanitised.srt", "SRT (*.srt)")[0]
            case = self.caseConv.currentText()
            caseConvert = {"None":"None", "UPPERCASE": "upper", "lowercase": "lower"}.get(case)
            keepCaps = list(self.keepCap.tags)
            puncToRemoveList = [self.puncList.item(i).text() for i in range(self.puncList.count()) if self.puncList.item(i).checkState() == Qt.CheckState.Checked]
            puncToRemove = f'[{"".join(puncToRemoveList)}]'
            censorWords = list(self.censor.tags)
            sanitise(inputFile, outputFile, keepCaps, puncToRemove, caseConvert, censorWords)

    def generateCaptions(self):
        if self.transcription == None:
            msgBox = QMessageBox()
            msgBox.setText("No transcription to make captions from.")
            msgBox.exec()
        else:
            maxWords = (self.maxWords.value())
            maxCharac = (self.maxCharacters.value())
            maxDur = (self.maxDuration.value()/10)
            fillGaps = (self.fillGaps.isChecked())
            self.captions = transcriptToCaptions(self.transcription, maxCharac, maxWords, maxDur, fillGaps)
            fileName = QFileDialog.getSaveFileName(self, "Choose location", "srt/captions.srt", "SRT (*.srt)")[0]
            transcriptionToSrt(self.captions, fileName)

    def transcribeButtonFunction(self):
        self.transcription = transcribe(self.inputVideoPath)
        fileName = QFileDialog.getSaveFileName(self, "Choose location", "srt/transcription.srt", "SRT (*.srt)")[0]
        transcriptionToSrt(self.transcription, fileName)
        wordLevelTiming = transcriptToCaptions(self.transcription, 100, 1, 10, False)
        transcriptionToSrt(wordLevelTiming, "srt/wordLevelTranscription.srt")
        self.videoTranscribed.emit()

    def playInput(self):
        self.inputPlayer.play()

    def pauseInput(self):
        self.inputPlayer.pause()

    def setInitialValues(self):
        self.videoProgress.setRange(0, self.inputPlayer.duration())
        self.videoProgressLabel.setText("00:00/00:00")
        self.subVideoProgressLabel.setText("00:00/00:00")
        self.transcription = None

    def updateInputVideoNav(self):
        self.videoProgress.setValue(self.inputPlayer.position())
        self.videoProgressLabel.setText(f"{milliToTimecode(self.inputPlayer.position())}/{milliToTimecode(self.inputPlayer.duration())}")

    def inputSliderReleased(self):
        self.inputPlayer.setPosition(self.videoProgress.value())
        self.inputPlayer.play()

    def changeSliderLabel(self, slider, label, div=1):
        label.setText(str(slider.value()/div))