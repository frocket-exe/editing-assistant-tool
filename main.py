from PySide6.QtWidgets import QApplication
import sys
import os
from gui.mainWindow import MainWindow
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

def createDirectories():
    directories = ["json", "edl", "srt", "media", "silent_video_segments", "censor"]
    for dir in directories:
        os.makedirs(os.path.join(PROJECT_DIR, dir), exist_ok=True)

if __name__ == "__main__":
    createDirectories()
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())