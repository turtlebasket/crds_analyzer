import numpy as np
from PyQt5 import QtWidgets
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import colors
from matplotlib import pyplot as plt
from db import mem
from crds_calc import exp_func

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        fig.tight_layout()
        self.fig_width = width
        self.fig_height = height
        self.fig_dpi = dpi
        super(MplCanvas, self).__init__(fig)

    def reset(self):
        self.axes.remove()
        self.axes = self.figure.add_subplot(111)
        self.figure.tight_layout()
        # fig = Figure(figsize=(self.fig_width, self.fig_height), dpi=self.fig_dpi)
        # self.axes = fig.add_subplot(111)
        # self.figure.clear()
        # self.figure.axes.remove()
        # fig.tight_layout()

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
        try:
            self.canv.axes.clear()
        except AttributeError:
            pass
        self.plot_data()
        self.canv.draw()

    def clear(self):
        self.canv.axes.clear()

class RawDataGraph(BaseGraph):
    pass

class VoltageGraph(BaseGraph):
    def plot_data(self):
        if not mem['v_data'][0] == None:
            self.canv.axes.plot(mem['x_data'], mem['v_data'], color='orange')

class PeaksGraph(BaseGraph):
    def plot_data(self):
        for i in mem['groups_correlated']:
            self.canv.axes.plot(i)

class AddedPeaksGraph(BaseGraph):

    params = {
        'peak_width': None,
        'shift_over': None
    }

    def set_params(self, peak_width, shift_over=0):
        self.params['peak_width'] = peak_width
        self.params['shift_over'] = shift_over

    def plot_data(self):
        self.canv.axes.plot(mem['added_peaks'], color='green') # plot added peaks

        if not self.params['peak_width'] == None: # plot peak indices
            for i in mem['peak_indices']: 
                self.canv.axes.axvspan(int(i-self.params['peak_width']/2+self.params['shift_over']), int(i+self.params['peak_width']/2+self.params['shift_over']), color='red', alpha=0.4)
                
class FitGraph(BaseGraph):
    def __init__(self, x):
        super().__init__(x)
        
    def set_peak_index(self, i):
        self.peak_index = i
        
    def plot_data(self):
        for g_i in range(len(mem['isolated_peaks'])):
            peak = mem['isolated_peaks'][g_i][self.peak_index]
            x_data = np.arange(len(peak))
            x_data_target = x_data[mem['overlayed_peak_indices'][g_i][self.peak_index]+mem['shift_over_fit']:]
            popt = mem['fit_equations'][g_i][self.peak_index]['popt']
            self.canv.axes.plot(peak)
            self.canv.axes.plot(x_data_target, exp_func(x_data_target, *popt), color='red')

class FitsGraphViewer(QtWidgets.QTabWidget):
    def __init__(self, x):
        super(FitsGraphViewer, self).__init__(x)
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

    def plot(self): # Create tabs & plot ALL data (each individual graph)
        self.clear()

        for p_i in range(len(mem['isolated_peaks'][0])):
            tab_name = str(p_i+1)
            fit_graph = FitGraph(self)
            fit_graph.set_peak_index(p_i)
            self.addTab(fit_graph, tab_name)
            fit_graph.plot()

# class FitsGraph(BaseGraph):
    
#     def __init__(self, x):
#         super(FitsGraph, self).__init__(x)
        
#     # def plot_data(self):
        
#     #     for g_i in range(len(mem['isolated_peaks'])):
#     #         for p_i in range(len(mem['isolated_peaks'][g_i])):
#     #             peak = mem['isolated_peaks'][g_i][p_i]
#     #             x_data = np.arange(len(peak))
#     #             popt = mem['fit_equations'][g_i][p_i]['popt']
#     #             self.canv.axes.plot(peak)
#     #             self.canv.axes.plot(x_data, exp_func(x_data, *popt), color='red')
    
#     def plot_data(self):

#         try:
#             self.canv.axes.remove()
#         except AttributeError:
#             pass

#         subplots_stacked = len(mem['isolated_peaks'][0]) # should all be same length
#         axes = self.canv.figure.subplots(subplots_stacked, 1, sharex=True)
        
#         for g_i in range(len(mem['isolated_peaks'])):
#             for p_i in range(subplots_stacked):
#                 peak = mem['isolated_peaks'][g_i][p_i]
#                 axes[p_i].plot(peak)
#                 # x_data = np.arange(len(peak))
#                 # popt = mem['fit_equations'][g_i][p_i]['popt']
#                 # axes[p_i].plot(x_data, exp_func(x_data, *popt), color='red')

#         # for ax in axs.flat:
#         #     ax.set(xlabel='x-label', ylabel='y-label')

class TimeConstantGraph(BaseGraph):

    def __init__(self, x):
        super().__init__(x)
        self.peak_index = 0
    
    def set_peak_index(self, i):
        self.peak_index = i

    def plot_data(self):
        data = []
        for g_i in range(len(mem['time_constants'])):
            data.append(mem['time_constants'][g_i][self.peak_index])
        self.canv.axes.hist(data, bins='auto', alpha=0.8)

class TimeConstantGraphsViewer(QtWidgets.QTabWidget):
    def __init__(self, x):
        super(TimeConstantGraphsViewer, self).__init__(x)
        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

    def plot(self): # Create tabs & plot ALL data (each individual graph)
        self.clear()

        for p_i in range(len(mem['time_constants'][0])):
            tab_name = str(p_i+1)
            tau_graph = TimeConstantGraph(self)
            tau_graph.set_peak_index(p_i)
            self.addTab(tau_graph, tab_name)
            tau_graph.plot()
