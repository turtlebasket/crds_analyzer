import sys
import crds_calc
from pandas import read_csv
from PyQt5 import QtGui, QtWidgets, QtCore
from memdb import mem
from mainwin import Ui_MainWindow
from widgets import BaseGraph
import pathlib

class AppWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    csv_selected = QtCore.pyqtSignal()
    correlation_complete = QtCore.pyqtSignal()
    fitting_complete = QtCore.pyqtSignal()

    def __init__(self):
        super(AppWindow, self).__init__()
        self.setupUi(self)

        # Graphing actions

        self.csv_selected.connect(self.raw_data_graph.plot)
        def corr_act():
            self.groups_graph.plot()
            self.graph_tabs.setCurrentIndex(1)
        self.correlation_complete.connect(corr_act)

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
            try:
                mem['v_data'] = data.transpose()[2]
            except IndexError:
                display_warning('No voltage column detected. VThreshold algo will not work.')

            self.groups_graph.clear()
            self.tau_graph.clear()
            self.graph_tabs.setCurrentIndex(0)
            self.csv_selected.emit()


        # Universal Actions stuff

        self.actionOpen_CSV_File.triggered.connect(select_csv)
        self.actionGithub_Repository.triggered.connect(lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl('https://github.com/turtlebasket/crds_analyze')))

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
                # mem['end_time'] = self.spin_end_time.value()
                self.spin_end_time.setDisabled(True)
        self.check_custom_end.stateChanged.connect(set_end_time)

        def init_correlate():
            groups_raw = None
            algo = self.combo_grouping_algo.currentIndex()
            try:
                if algo == 0:
                    display_error('VThreshold not yet implemented.')
                    return
                elif algo == 1:
                    try:
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
                    except (ValueError, TypeError):
                        display_error('Failed to correlate. This could be because no groups are being detected.')

                mem['groups_correlated'] = crds_calc.correlate_groups(groups_raw)
                self.correlation_complete.emit()

            except KeyError:
                display_error('Failed to correlate. Did you import a data file & set parameters?')
        self.correlate_button.pressed.connect(init_correlate)

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