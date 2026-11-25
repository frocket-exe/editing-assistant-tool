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
    QToolButton
    )
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QBrush, QIcon
from PySide6.QtCore import QSize, Qt, QTimer, Signal, Slot
from pathlib import Path
import sys
from .tab import Tab, AspectRatioLayout, milliToTimecode
from .flowLayout import FlowLayout
from scripts.transcribe import transcribe, transcriptionToSrt, transcriptToCaptions, sanitise
import json


class TagChip(QFrame):
    closed = Signal(str)
    def __init__(self, tag, parent=None):
        super().__init__(parent)
        self.tag = tag

        label = QLabel(tag)

        closeButton = QToolButton()
        closeButton.setText('\u2715')
        closeButton.setCursor(Qt.CursorShape.PointingHandCursor)
        closeButton.setAutoRaise(True)
        closeButton.clicked.connect(lambda: self.closed.emit(self.tag))

        layout = QHBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(closeButton)


class TagBar(QWidget):
    tagsChanged = Signal(set)
    def __init__(self, parent=None, placeholder="Add tag...", complete=[]):
        super().__init__(parent)
        self._tags = set()
        self.buttons = {}

        self.tagInput = QLineEdit()
        self.tagInput.setPlaceholderText(placeholder)
        self.tagInput.returnPressed.connect(self.onPress)
        self.completer = QCompleter(complete)
        self.tagInput.setCompleter(self.completer)

        tagsContainer = QWidget()
        self.tagLayout = FlowLayout(tagsContainer)

        self.bigLayout = QVBoxLayout(self)
        self.bigLayout.addWidget(tagsContainer)
        self.bigLayout.addWidget(self.tagInput)
        # self.setFocusProxy(self.tagInput)

    @property
    def tags(self):
        return set(self._tags)

    @tags.setter
    def tags(self, new_tags):
        if new_tags == self._tags:
            return
        self.blockSignals(True)
        self.clear_buttons()
        self._tags = set(new_tags)
        for tag in sorted(self._tags):
            self.create_button(tag)
        self.blockSignals(False)

    @Slot()
    def add_tag(self, tag):
        tag = tag.strip()
        if not tag or tag in self._tags:
            self.tagInput.clear()
            return
        self._tags.add(tag)
        self.create_button(tag)
        self.tagInput.clear()
        self.tagsChanged.emit(set(self._tags))

    def remove_tag(self, tag):
        if tag not in self._tags:
            return
        self._tags.discard(tag)
        button = self.buttons.pop(tag, None)
        if button:
            self.tagLayout.removeWidget(button)
            button.deleteLater()
        self.tagsChanged.emit(set(self._tags))

    def create_button(self, tag):
        chip = TagChip(tag)
        chip.closed.connect(self.remove_tag)
        self.buttons[tag] = chip
        self.tagLayout.addWidget(chip)

    def clear_buttons(self):
        for button in self.buttons.values():
            self.tagLayout.removeWidget(button)
            button.deleteLater()
        self.buttons.clear()

    @Slot()
    def onPress(self):
        self.add_tag(self.tagInput.text())
        self.tagInput.setFocus()


class TranscribeTab(Tab):
    def __init__(self, title):
        super().__init__(title)

        self.inputPlayer.positionChanged.connect(self.updateInputVideoNav)

        inputAspectContainer = QWidget()
        inputAspectContainer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        inputAspectLayout = AspectRatioLayout(4/3, inputAspectContainer)
        inputAspectLayout.addWidget(self.inputVideo)

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
        westSide.addWidget(inputAspectContainer)
        westSide.addWidget(navigationContainer)
        westSide.addWidget(transcribeButton)
        westSide.addWidget(maxWordsContainer)
        westSide.addWidget(maxCharactersContainer)
        westSide.addWidget(maxDurationContainer)
        westSide.addWidget(createSubsButton)

        self.subVideo = QVideoWidget()
        self.subAudio = QAudioOutput()
        self.subPlayer = QMediaPlayer()
        self.subPlayer.setAudioOutput(self.subAudio)
        self.subPlayer.setVideoOutput(self.subVideo)
        # self.subPlayer.positionChanged.connect(self.updateSubVideoNav)
        
        subAspectContainer = QWidget()
        subAspectContainer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        subAspectLayout = AspectRatioLayout(4/3, subAspectContainer)
        subAspectLayout.addWidget(self.subVideo)

        subNavigationContainer = QWidget()
        subNavigation = QHBoxLayout(subNavigationContainer)
        subPlayButton = QPushButton()
        subPlayButton.setIcon(QIcon(QPixmap("gui/icons/play.png")))
        # subPlayButton.clicked.connect(self.playSub)
        subPauseButton = QPushButton()
        subPauseButton.setIcon(QIcon(QPixmap("gui/icons/pause.png")))
        # subPauseButton.clicked.connect(self.pauseSub)
        self.subVideoProgress = QSlider(Qt.Orientation.Horizontal)
        # self.subVideoProgress.sliderPressed.connect(self.subSliderPressed)
        # self.subVideoProgress.sliderReleased.connect(self.subSliderReleased)
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
        burnButton = QPushButton("Add subtitles to video")


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

    def setInitialValues(self):
        self.videoProgressLabel.setText("00:00/00:00")
        self.subVideoProgressLabel.setText("00:00/00:00")

    def updateInputVideoNav(self):
        pass