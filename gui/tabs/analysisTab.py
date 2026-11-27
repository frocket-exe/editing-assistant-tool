from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QFileDialog
from PySide6.QtCore import QSize, Qt
from pathlib import Path
import sys
from .tab import Tab
from scripts.analysis import visualize
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure



class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)



class AnalysisTab(Tab):
    def __init__(self, title, inputVideoPath, cutVideoPath):
        super().__init__(title)
        self.inputVideoPath = inputVideoPath
        self.cutVideoPath = cutVideoPath
        beforePlot = visualize(self.inputVideoPath)
        afterPlot = visualize(self.cutVideoPath)

        beforeLabel = QLabel("Audio before cuts:")
        beforeChart = MplCanvas(self, width=5, height=4, dpi=100)
        beforePlot.plot(ax=beforeChart.axes)

        afterLabel = QLabel("Audio after cuts:")
        afterChart = MplCanvas(self, width=5, height=4, dpi=100)
        afterPlot.plot(ax=afterChart.axes)

        layout = QVBoxLayout(self)
        layout.addWidget(beforeLabel)
        layout.addWidget(beforeChart)
        layout.addWidget(afterLabel)
        layout.addWidget(afterChart)