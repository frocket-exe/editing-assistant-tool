from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QLayout, QLabel, QToolButton, QHBoxLayout, QFrame, QToolButton, QCheckBox, QMessageBox, QLineEdit, QCompleter, QVBoxLayout
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import QSize, Qt, QRect, QUrl, Signal, Slot
import json
from .flowLayout import FlowLayout


class Tab(QWidget):
    def __init__(self, title):
        super().__init__()

        self.title = title
        self.setWindowTitle(title)
        self.setMinimumSize(QSize(925, 625))

        self.inputVideo = QVideoWidget()
        self.inputAudio = QAudioOutput()
        self.inputPlayer = QMediaPlayer()
        self.inputPlayer.setAudioOutput(self.inputAudio)
        self.inputPlayer.setVideoOutput(self.inputVideo)

    def setInputVideo(self):
        with open("json/videoMetrics.json", "r") as f:
            data = json.load(f)
        self.inputVideoPath = data["path"]
        self.inputPlayer.setSource(QUrl.fromLocalFile(self.inputVideoPath))
        self.inputPlayer.pause()


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