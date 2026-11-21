from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import QSize, Qt
from pathlib import Path
import sys
from .tab import Tab
import json


class ImportTab(Tab):
    def __init__(self, title):
            super().__init__(title)

            selectVideoButton = QPushButton("Select video")
            selectVideoButton.clicked.connect(self.updateInfoLabel)
            buttonResponse = QLabel("Video imported successfully")
            self.videoInfo = QLabel()
            self.audioInfo = QLabel()

            layout = QVBoxLayout()
            infoContainer = QWidget()
            subLayout = QHBoxLayout(infoContainer)
            layout.addWidget(selectVideoButton)
            layout.addWidget(buttonResponse)

            subLayout.addWidget(self.videoInfo)
            subLayout.addWidget(self.audioInfo)
            layout.addWidget(infoContainer)

            self.setLayout(layout)

            self.setObjectName("ImportTab")
            selectVideoButton.setObjectName("SelectVideoButton")
            self.videoInfo.setObjectName("VideoInfo")
            self.audioInfo.setObjectName("AudioInfo")

            stylePath = Path(__file__).resolve().parent.parent / "styles" / "import.qss"
            with open(stylePath, "r") as f:
                self.setStyleSheet(f.read())

    def updateInfoLabel(self):
        videoInfo, audioInfo = self.jsonToStr()
        self.videoInfo.setText(videoInfo)
        self.audioInfo.setText(audioInfo)

    def jsonToStr(self):
        with open("json/videoMetrics.json", "r") as f:
            data = json.load(f)
        videoInfo = ("Video:\n"
                   f"Codec Name: {data["video"]["codec_name"]}\n"
                   f"Long Codec Name: {data["video"]["codec_long_name"]}\n"
                   f"Duration: {float(data["video"]["duration"]):.2f}s\n"
                   f"Bit rate: {data["video"]["bit_rate"]}\n"
                   f"Resolution: {data["video"]["width"]}x{data["video"]["height"]}\n"
                   f"Frame rate: {data["video"]["r_frame_rate"][:-2]}\n")
        audioInfo = (f"Audio:\n"
                   f"Codec name: {data["audio"]["codec_name"]}\n"
                   f"Long Codec Name: {data["audio"]["codec_long_name"]}\n"
                   f"Bit rate: {data["audio"]["bit_rate"]}\n"
                   f"Sample rate: {data["audio"]["sample_rate"]}\n"
                   f"Channels: {data["audio"]["channels"]}\n")
        return videoInfo, audioInfo