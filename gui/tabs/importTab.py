from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QVBoxLayout, QLabel
from PySide6.QtCore import QSize, Qt
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
            layout.addWidget(selectVideoButton)
            layout.addWidget(buttonResponse)
            layout.addWidget(self.videoInfo)
            layout.addWidget(self.audioInfo)

            self.setLayout(layout)

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