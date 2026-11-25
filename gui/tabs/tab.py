from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QLayout
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import QSize, Qt, QRect, QUrl
import json


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
        self.setInputVideo()

    def setInputVideo(self):
        with open("json/videoMetrics.json", "r") as f:
            data = json.load(f)
        self.inputVideoPath = data["path"]
        self.inputPlayer.setSource(QUrl.fromLocalFile(self.inputVideoPath))


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