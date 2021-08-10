import sys
import crds_calc
from pandas import read_csv
from PyQt5 import QtGui, QtWidgets, QtCore
from db import mem
from mainwin import Ui_MainWindow
from widgets import BaseGraph
import pathlib
from re import search as re_search
from varname.core import nameof
from hashlib import md5
from sqlitedict import SqliteDict

class AppWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super(AppWindow, self).__init__()
        self.setupUi(self)

        # Define syncables
        synced_value_widgets = []
        synced_check_widgets = []
        for wname in vars(self):
            w = vars(self).get(wname)
            if re_search(r"^spin\_(.*)$", wname) != None:
                synced_value_widgets.append(w)
            elif re_search(r"^check\_(.*)$", wname) != None:
                synced_check_widgets.append(w)

        # Helpers

        def display_warning(message: str):
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
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

        def select_csv():
            filename, _ = QtWidgets.QFileDialog.getOpenFileName(self)
            data = None
            try:
                data = read_csv(filename, comment="%", delimiter=";").to_numpy()
            except:
                return
            mem['x_data'] = data.transpose()[0]
            mem['y_data'] = data.transpose()[1]
            # timestep = mem['x_data'][1] - mem['x_data'][0]
            timestep = (mem['x_data'][-1] - mem['x_data'][0]) / len(mem['x_data'])
            mem['timestep'] = timestep
            self.spin_timestep.setValue(timestep)
            print(timestep)
            self.raw_data_graph.plot() # Graph new stuff

            # self.groups_graph.clear() # Clear old stuff
            self.voltage_graph.clear()
            self.added_peaks_graph.clear()
            # self.tau_graph.clear()

            mem['ymin'], mem['ymax'] = crds_calc.minmax(mem['y_data'])

            try:
                mem['v_data'] = data.transpose()[2]
                self.voltage_graph.plot()
                self.graph_tabs.setCurrentIndex(1)
            except IndexError:
                display_warning('No voltage column detected. VThreshold algo will not work.')
                self.voltage.setVisible(False)
                self.graph_tabs.setCurrentIndex(0)

            # Load from persistent storage & bind write actions

            # path_hash = md5(filename.encode('utf-8')).hexdigest()

            # def set_value(name, val):
            #     with SqliteDict(f"./db/{path_hash}.sqlite", autocommit=True) as storage:
            #         print(f"Change {name} to {val}.")
            #         storage[name] = val
            #         print(f"Check: {storage[name]}")

            # with SqliteDict(f"./db/{path_hash}.sqlite", autocommit=True) as storage:

            #     for w in synced_value_widgets:
            #         name = w.objectName()
            #         try:
            #             w.setValue(bool(storage[name]))
            #             print(f"Loaded {name}.")
            #         except KeyError:
            #             print(f"Failed to load object {name}.")
            #             pass
            #         w.valueChanged.connect(lambda x: set_value(name, x))

            #     for w in synced_check_widgets:
            #         name = w.objectName()
            #         try:
            #             w.setChecked(storage[name])
            #             print(f"Loaded {name}.")
            #         except KeyError:
            #             print(f"Failed to load object {name}.")
            #             pass
            #         w.stateChanged.connect(lambda: set_value(name, w.isChecked()))

        # Universal Actions stuff

        self.actionOpen_CSV_File.triggered.connect(select_csv)
        self.actionGithub_Repository.triggered.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl('https://github.com/turtlebasket/crds_analyze')))

        # NOTE: Do later, use QDialog
        # def check_if_quit():
        #   <stuff here>
        self.actionQuit_2.triggered.connect(sys.exit)

        # Inputs

        def switch_grouping_algo():
            algo = self.combo_grouping_algo.currentIndex()
            self.grouping_config_area.setCurrentIndex(algo)
        self.combo_grouping_algo.currentIndexChanged.connect(switch_grouping_algo)

        def set_start_time():
            if self.check_custom_start.isChecked():
                self.spin_start_time.setDisabled(False)
            else:
                self.spin_start_time.setDisabled(True)
        self.check_custom_start.stateChanged.connect(set_start_time)

        def set_end_time():
            if self.check_custom_end.isChecked():
                self.spin_end_time.setDisabled(False)
            else:
                self.spin_end_time.setDisabled(True)
        self.check_custom_end.stateChanged.connect(set_end_time)


        # Sync up peak detection settings between input locations
        self.spin_min_peakheight.valueChanged.connect(lambda x: self.spin_min_peakheight_2.setValue(x))
        self.spin_min_peakheight_2.valueChanged.connect(lambda x: self.spin_min_peakheight.setValue(x))
        self.spin_min_peakprominence.valueChanged.connect(lambda x: self.spin_min_peakprominence_2.setValue(x))
        self.spin_min_peakprominence_2.valueChanged.connect(lambda x: self.spin_min_peakprominence.setValue(x))
        self.spin_moving_average_denom.valueChanged.connect(lambda x: self.spin_moving_average_denom_2.setValue(x))
        self.spin_moving_average_denom_2.valueChanged.connect(lambda x: self.spin_moving_average_denom.setValue(x))
        
        # Make advanced peak detection optional
        def update_advanced_peak_detection_setting():
            enabled = self.check_advanced_peak_detection.isChecked()
            self.spin_min_peakheight_2.setEnabled(enabled)
            self.spin_min_peakprominence_2.setEnabled(enabled)
            self.spin_moving_average_denom_2.setEnabled(enabled)
        self.check_advanced_peak_detection.stateChanged.connect(update_advanced_peak_detection_setting)


        def init_correlate():
            groups_raw = None
            algo = self.combo_grouping_algo.currentIndex()
            try:
                if algo == 0:
                    groups_raw = crds_calc.vthreshold(
                        mem['x_data'],
                        mem['y_data'],
                        mem['v_data'],
                        self.spin_min_voltage.value(),
                        self.spin_max_voltage.value(),
                        mirrored=False if self.check_skip_groups.checkState() == 0 else True,
                        start=self.spin_start_time.value() if self.check_custom_start.isChecked() else None,
                        end=self.spin_end_time.value() if self.check_custom_end.isChecked() else None
                    )
                    # display_error('VThreshold not yet implemented.')
                    # return

                elif algo == 1:
                    groups_raw = crds_calc.spaced_groups(
                        mem['x_data'],
                        mem['y_data'],
                        self.spin_group_len.value(),
                        self.spin_min_peakheight.value(),
                        self.spin_min_peakprominence.value(),
                        self.spin_moving_average_denom.value(),
                        mirrored=False if self.check_skip_groups.checkState() == 0 else True,
                        start=self.spin_start_time.value() if self.check_custom_start.isChecked() else None,
                        end=self.spin_end_time.value() if self.check_custom_end.isChecked() else None
                    )

                if groups_raw == None or len(groups_raw) < 1:
                    display_error("No groups were detected. Try adjusting grouping parameters.")

                mem['groups_correlated'] = crds_calc.correlate_groups(groups_raw)

                # Graphing action
                self.groups_graph.plot()
                self.graph_tabs.setCurrentIndex(2)

            except KeyError:
                display_error('Failed to correlate. Did you import a data file & set parameters?')
        self.correlate_button.pressed.connect(init_correlate)

        def init_add_simple():
            try:
                mem['added_peaks'] = crds_calc.add_peaks_only(mem['groups_correlated'])

                self.added_peaks_graph.set_params(None, shift_over=None)
                self.added_peaks_graph.plot()
                self.graph_tabs.setCurrentIndex(3)

            except KeyError:
                display_error("Correlated groups not found. Group peaks first.")
        self.peak_add_button.pressed.connect(init_add_simple)
            

        def init_add():
            try:
                mem['added_peaks'], mem['peak_indices'], mem['isolated_peaks'] = crds_calc.isolate_peaks(
                    mem['groups_correlated'],
                    self.spin_peak_overlap.value(),
                    self.spin_moving_average_denom.value(),
                    peak_prominence=self.spin_min_peak_height_added.value(),
                    peak_minheight=self.spin_peak_prominence_added.value(),
                    shift_over=self.spin_shift_over.value()
                )
                self.added_peaks_graph.set_params(self.spin_peak_overlap.value(), shift_over=self.spin_shift_over.value())
                self.added_peaks_graph.plot()
                self.graph_tabs.setCurrentIndex(3)

            except KeyError:
                display_error("Correlated groups not found. Group peaks first.")
        self.isolate_button.pressed.connect(init_add)

        def init_fit():
            if not 'isolated_peaks' in mem:
                display_error('Peaks not yet isolated.')
                return
            mem['fit_equations'] = crds_calc.fit_peaks(
                mem['isolated_peaks'],
                mem['peak_indices'],
                self.spin_min_peakheight_2.value(),
                self.spin_min_peakprominence_2.value(),
                self.spin_moving_average_denom_2.value(),
                self.spin_var_a.value(),
                self.spin_var_tau.value(),
                self.spin_var_y0.value(),
                self.spin_shift_over_fit.value(),
                self.check_advanced_peak_detection.isChecked()
            )
            mem['shift_over_fit'] = self.spin_shift_over_fit.value()
            # print(mem['fit_equations'])
            self.peak_fit_viewer.plot()

            mem['time_constants'] = crds_calc.get_time_constants(mem['fit_equations'])
            self.tau_viewer.plot()

            self.graph_tabs.setCurrentIndex(5)
        self.fit_button.pressed.connect(init_fit)

        # Show equation

        pix = QtGui.QPixmap(f"{pathlib.Path(__file__).parent.resolve()}/assets/eq3.png")
        item = QtWidgets.QGraphicsPixmapItem(pix)
        item.setScale(0.38)
        scene = QtWidgets.QGraphicsScene()
        scene.addItem(item)
        self.equation_view.setScene(scene)

        # Show self

        self.show()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec_())