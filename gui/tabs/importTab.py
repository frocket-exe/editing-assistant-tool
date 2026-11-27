from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QFileDialog
from PySide6.QtCore import Qt, Signal
from pathlib import Path
from .tab import Tab
from scripts.getProperties import getProperties
import json


# Import Tab Class inherits from Tab class
class ImportTab(Tab):
    # Custom signal to report to mainWindow.py when a video has been imported
    videoImported = Signal(str)

    def __init__(self, title):
        super().__init__(title)

        # Create GUI elements
        selectVideoButton = QPushButton("Select video")
        selectVideoButton.clicked.connect(self.openFile)
        self.buttonResponse = QLabel()
        self.buttonResponse.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.buttonResponse.setWordWrap(True)
        videoTitle =  QLabel("Video")
        audioTitle = QLabel("Audio")
        self.videoInfo = QLabel()
        self.videoInfo.setWordWrap(True)
        self.videoInfo.setAlignment(Qt.AlignTop)
        self.audioInfo = QLabel()
        self.audioInfo.setWordWrap(True)
        self.audioInfo.setAlignment(Qt.AlignTop)

        # Organise GUI elements in layout
        # Main layout is a VBox - widgets laid on top of one another in rows
        layout = QVBoxLayout()
        infoContainer = QWidget()
        videoContainer = QWidget()
        audioContainer = QWidget()
        videoLayout = QVBoxLayout(videoContainer)
        audioLayout = QVBoxLayout(audioContainer)
        subLayout = QHBoxLayout(infoContainer)
        layout.addWidget(selectVideoButton)
        layout.addWidget(self.buttonResponse)

        videoLayout.addWidget(videoTitle)
        videoLayout.addWidget(self.videoInfo)
        subLayout.addWidget(videoContainer)
        audioLayout.addWidget(audioTitle)
        audioLayout.addWidget(self.audioInfo)
        subLayout.addWidget(audioContainer)
        layout.addWidget(infoContainer)

        # Allow the informational sections to take 3/4 of empty space when resizing windows
        # Import button takes the other 1/4 of the empty space
        # Keeps some margin between the information sections
        layout.setStretch(0, 1)
        layout.setStretch(1, 0)
        layout.setStretch(2, 3)
        subLayout.setSpacing(15)

        # Ensures correct resizing of elements
        videoTitle.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        audioTitle.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.videoInfo.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.audioInfo.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

        self.setLayout(layout)

        # Setting object names of GUI elements to add custom styling with Qt Style Sheet (styles/import.qss)
        self.setObjectName("ImportTab")
        selectVideoButton.setObjectName("SelectVideoButton")
        self.buttonResponse.setObjectName("Response")
        self.videoInfo.setObjectName("VideoInfo")
        self.audioInfo.setObjectName("AudioInfo")
        videoTitle.setObjectName("VideoTitle")
        audioTitle.setObjectName("AudioTitle")

        # Import QSS for custom styling
        stylePath = Path(__file__).resolve().parent.parent / "styles" / "import.qss"
        with open(stylePath, "r") as f:
            self.setStyleSheet(f.read())

    # Function to validate and open file - connected to import video button
    def openFile(self):
        # Sanitisation - only allows video files
        allowedFileTypes = [".mp4", ".mkv", ".mov"]
        fileName = QFileDialog.getOpenFileName(self, "Open File", "media/", f"Video Files ({" ".join([("*"+ext) for ext in allowedFileTypes])});; All Files (*.*)")[0]
        fileExists = (fileName != '')
        # Validation - only proceeds if the file exists
        if fileExists:
            fileExt = Path(fileName).suffix
            if fileExt in allowedFileTypes:
                # Write metadata properties to json/videoMetrics.json
                getProperties(fileName)
                # Confirm to user that the file has been imported correctly
                fileShortName = Path(fileName).stem + Path(fileName).suffix
                self.buttonResponse.setText(f"Video imported successfully - {fileShortName}")
                self.buttonResponse.setProperty("status", "success")
                self.buttonResponse.style().unpolish(self.buttonResponse)
                self.buttonResponse.style().polish(self.buttonResponse)
                # Call labels to be updated with newly gathered info
                self.updateInfoLabel()
                self.videoImported.emit(fileName)
            else:
                # Highlight to user that the file has not been correctly imported
                self.buttonResponse.setText("This is not an allowed file type.")
                self.buttonResponse.setProperty("status", "error")
                self.buttonResponse.style().unpolish(self.buttonResponse)
                self.buttonResponse.style().polish(self.buttonResponse)
                # Reset information boxes to show new video has been attempted to be imported
                self.videoInfo.setText("")
                self.audioInfo.setText("")

    # Update info boxes
    def updateInfoLabel(self):
        videoInfo, audioInfo = self.jsonToStr()
        self.videoInfo.setText(videoInfo)
        self.audioInfo.setText(audioInfo)

    # Read json/videoMetrics.json and return a nicely formatted string showing the information
    def jsonToStr(self):
        with open("json/videoMetrics.json", "r") as f:
            data = json.load(f)
        videoInfo = (f"Codec Name: {data["video"]["codec_name"]}\n"
                   f"Long Codec Name: {data["video"]["codec_long_name"]}\n"
                   f"Duration: {float(data["video"]["duration"]):.2f}s\n"
                   f"Bit rate: {data["video"]["bit_rate"]}\n"
                   f"Resolution: {data["video"]["width"]}x{data["video"]["height"]}\n"
                   f"Frame rate: {data["video"]["r_frame_rate"][:-2]}\n")
        audioInfo = (f"Codec name: {data["audio"]["codec_name"]}\n"
                   f"Long Codec Name: {data["audio"]["codec_long_name"]}\n"
                   f"Bit rate: {data["audio"]["bit_rate"]}\n"
                   f"Sample rate: {data["audio"]["sample_rate"]}\n"
                   f"Channels: {data["audio"]["channels"]}\n")
        return videoInfo, audioInfo