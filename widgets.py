from PyQt5 import QtWidgets
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from memdb import mem

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        fig.tight_layout()
        super(MplCanvas, self).__init__(fig)

class BaseGraph(QtWidgets.QWidget):
    """
    Widget with embedded matplotlib graph & navigation toolbar

    Reference: https://www.mfitzp.com/tutorials/plotting-matplotlib/
    """

    canv = None

    def __init__(self, x):
        super().__init__(x)
        self.canv = MplCanvas(self)
        # Example
        # canv.axes.plot([0,1,2,3,4], [10,1,20,3,40])
        toolbar = NavigationToolbar(self.canv, self)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.canv)
        self.setLayout(layout)

    def plot_data(self):
        self.canv.axes.plot(mem['x_data'], mem['y_data'])

    def plot(self):
        self.canv.axes.clear()
        self.plot_data()
        self.canv.draw()
        print("attempted plot")

    def clear(self):
        self.canv.axes.clear()
        self.canv.draw()

class RawDataGraph(BaseGraph):
    pass

class PeaksGraph(BaseGraph):
    def plot_data(self):
        for i in mem['groups_correlated']:
            self.canv.axes.plot(i)

class TimeConstantGraph(BaseGraph):
    pass # no modifications thus far