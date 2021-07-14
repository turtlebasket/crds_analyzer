import numpy as np
from pandas import read_csv
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import crds_calc
import PyQt5
from PyQt5 import QtWidgets, QtCore
from memdb import mem
import pathlib

# Helper functions

def display_warning(message: str):
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.warning)
    msg.setText("Warning")
    msg.setInformativeText(message)
    msg.setWindowTitle("Warning")
    msg.exec_()

def display_error(message: str):
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Critical)
    msg.setText("Error")
    msg.setInformativeText(message)
    msg.setWindowTitle("Error")
    msg.exec_()

# Create global object to send signals

class Global(QtWidgets.QWidget):
    grouping_algo_changed = QtCore.pyqtSignal()
    csv_selected = QtCore.pyqtSignal()
    correlation_complete = QtCore.pyqtSignal()
    fitting_complete = QtCore.pyqtSignal()
globj = Global()

# Menu definitions

class file_menu(QtWidgets.QMenu):
    def __init__(self, x):
        super().__init__(x)
        open_csv = QtWidgets.QAction("Open CSV File", self)
        open_csv.setShortcut("Ctrl+O")
        open_csv.triggered.connect(self.select_csv)
        self.addAction(open_csv)

    def select_csv(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self)
        data = read_csv(filename, comment="%", delimiter=";").to_numpy()
        mem['x_data'] = data.transpose()[0]
        mem['y_data'] = data.transpose()[1]
        try:
            mem['v_data'] = data[2].transpose()
        except IndexError:
            display_error('No voltage column detected. Functionality will be limited.')

        globj.csv_selected.emit()

class help_menu(QtWidgets.QMenu):
    def __init__(self, x):
        super().__init__(x)
        visit_repo = QtWidgets.QAction("Go to GitHub Repo", self)
        visit_repo.triggered.connect(self.go_to_repo)
        self.addAction(visit_repo)

    def go_to_repo(self):
        PyQt5.QtGui.QDesktopServices.openUrl(QtCore.QUrl('https://github.com/turtlebasket/crds_analyze'))

# Inputs / Parameter boxes

class combo_grouping_algo(QtWidgets.QComboBox):
    def change(self):
        mem['grouping_algo'] = self.currentIndex()
        globj.grouping_algo_changed.emit()
    def __init__(self, x):
        super().__init__(x)
        self.currentIndexChanged.connect(self.change)

class config_area(QtWidgets.QStackedWidget):
    def __init__(self, x):
        super().__init__(x)
        self.setCurrentIndex(0)
        globj.grouping_algo_changed.connect(lambda: self.setCurrentIndex(mem['grouping_algo']))

class spin_min_voltage(QtWidgets.QDoubleSpinBox):
    def changeVal(self, val):
        mem['min_voltage'] = float(val)
    def __init__(self, x):
        super().__init__(x)
        mem['min_voltage'] = float(self.value())
        self.textChanged.connect(self.changeVal)

class spin_group_len(QtWidgets.QDoubleSpinBox):
    def changeVal(self, val):
        mem['group_len'] = float(val)
    def __init__(self, x):
        super().__init__(x)
        mem['group_len'] = float(self.value())
        self.textChanged.connect(self.changeVal)

class spin_peak_len(QtWidgets.QDoubleSpinBox):
    def changeVal(self, val):
        mem['peak_len'] = float(val)
    def __init__(self, x):
        super().__init__(x)
        mem['peak_len'] = float(self.value())
        self.textChanged.connect(self.changeVal)

class spin_min_peakheight(QtWidgets.QDoubleSpinBox):
    def changeVal(self, val):
        mem['peak_minheight'] = float(val)
    def __init__(self, x):
        super().__init__(x)
        mem['peak_minheight'] = float(self.value())
        self.textChanged.connect(self.changeVal)

class spin_min_peakprominence(QtWidgets.QDoubleSpinBox):
    def changeVal(self, val):
        mem['peak_prominence'] = float(val)
    def __init__(self, x):
        super().__init__(x)
        mem['peak_prominence'] = float(self.value())
        self.textChanged.connect(self.changeVal)

class spin_moving_average_denom(QtWidgets.QSpinBox):
    def changeVal(self, val):
        mem['moving_avg_denom'] = int(val)
        print(isinstance(val, str))
    def __init__(self, x):
        super().__init__(x)
        mem['moving_avg_denom'] = float(self.value())
        self.textChanged.connect(self.changeVal)

class equation_view(QtWidgets.QGraphicsView):
    def __init__(self, x):
        super().__init__(x)
        pix = PyQt5.QtGui.QPixmap(f"{pathlib.Path(__file__).parent.resolve()}/assets/eq2.png")
        item = QtWidgets.QGraphicsPixmapItem(pix)
        item.setScale(0.15)
        scene = QtWidgets.QGraphicsScene()
        scene.addItem(item)
        self.setScene(scene)

class correlate_button(QtWidgets.QPushButton):
    def calc(self):
        groups_raw = None
        try:
            if (mem['grouping_algo'] == 0):
                display_error('VThreshold not yet implemented.')
            elif (mem['grouping_algo'] == 1):
                groups_raw = crds_calc.spaced_groups(
                    mem['x_data'],
                    mem['y_data'],
                    mem['group_len'],
                    mem['peak_minheight'],
                    mem['peak_prominence'],
                    mem['moving_avg_denom']
                )

            mem['groups_correlated'] = crds_calc.correlate_groups(groups_raw)
            globj.correlation_complete.emit()

        except KeyError:
            display_error('Failed to correlate. Did you import a data file & set parameters?')


    def __init__(self, x):
        super().__init__(x)
        self.pressed.connect(self.calc)

class fit_button(QtWidgets.QPushButton):
    def fit(self):
        print("hi")
    def __init__(self, x):
        super().__init__(x)
        self.pressed.connect(self.fit)


# Graph stuff

class graph_tab(QtWidgets.QTabWidget):
    def __init__(self, x):
        super().__init__(x)
        globj.csv_selected.connect(lambda: self.setCurrentIndex(0))
        globj.correlation_complete.connect(lambda: self.setCurrentIndex(1))
        globj.fitting_complete.connect(lambda: self.setCurrentIndex(2))

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        fig.tight_layout()
        super(MplCanvas, self).__init__(fig)

class base_graph(QtWidgets.QWidget):
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

    def plot(self):
        self.canv.axes.plot(mem['x_data'], mem['y_data'])

    def plot_full(self):
        self.canv.axes.clear()
        self.plot()
        self.canv.draw()
        print("attempted plot")

class rawdata_graph(base_graph):
    def __init__(self, x):
        super().__init__(x)
        globj.csv_selected.connect(self.plot_full)

class peaks_graph(base_graph):
    def __init__(self, x):
        super().__init__(x)
        globj.correlation_complete.connect(self.plot_full)

    def plot(self):
        for i in mem['groups_correlated']:
            self.canv.axes.plot(i)


class timeconstant_graph(base_graph):
    pass