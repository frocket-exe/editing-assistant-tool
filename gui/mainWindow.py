from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QTabWidget
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPalette, QColor
import sys
from tabs.importTab import ImportTab


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")
        self.setMinimumSize(QSize(925, 625))

        self.tabs = QTabWidget()
        self.importTab = ImportTab("Import")
        self.importTab2 = ImportTab("Export")
        self.tabs.addTab(self.importTab, self.importTab.title)
        self.tabs.addTab(self.importTab2, self.importTab2.title)

        self.setCentralWidget(self.tabs)


app = QApplication(sys.argv)

# window = MainWindow()
window = ImportTab("Tab 1 - Import")
window.show()

app.exec()