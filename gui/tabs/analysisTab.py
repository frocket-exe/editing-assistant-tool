from PySide6.QtWidgets import QLabel, QVBoxLayout
from .tab import Tab
from scripts.analysis import visualize
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure


# Class inheriting from FigureCanvas to embed matplotlib graphs
# taken from a tutorial on the Qt6 officials docs
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


# Analysis Tab inherits from custom Tab class
class AnalysisTab(Tab):
    def __init__(self, title, inputVideoPath, cutVideoPath):
        super().__init__(title)
        # Set input video and cut video paths
        self.inputVideoPath = inputVideoPath
        self.cutVideoPath = cutVideoPath
        # Get plot of the audio waveforms from video path
        beforePlot = visualize(self.inputVideoPath)
        afterPlot = visualize(self.cutVideoPath)

        # Before edits title and chart
        beforeLabel = QLabel("Audio before cuts:")
        beforeChart = MplCanvas(self, width=5, height=4, dpi=100)
        beforePlot.plot(ax=beforeChart.axes)

        # After edits title and chart
        afterLabel = QLabel("Audio after cuts:")
        afterChart = MplCanvas(self, width=5, height=4, dpi=100)
        afterPlot.plot(ax=afterChart.axes)

        # Add titles and chart to layout
        # Layout is a VBox - widgets appear in rows
        layout = QVBoxLayout(self)
        layout.addWidget(beforeLabel)
        layout.addWidget(beforeChart)
        layout.addWidget(afterLabel)
        layout.addWidget(afterChart)