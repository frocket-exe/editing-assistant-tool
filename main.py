from PySide6.QtWidgets import QApplication
import sys
import os
# from gui.mainWindow import MainWindow
import gui.mainWindow
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

def createDirectories():
    directories = ["json", "edl", "srt", "media", "silent_video_segments", "censor"]
    for dir in directories:
        os.makedirs(os.path.join(PROJECT_DIR, dir), exist_ok=True)

if __name__ == "__main__":
    createDirectories()
    # app = QApplication(sys.argv)

    # window = MainWindow()
    # window = ImportTab("Import")
    # window = SilenceTab("Silences")
    # window = TranscribeTab("Transcribe")
    # window.show()

    # sys.exit(app.exec())