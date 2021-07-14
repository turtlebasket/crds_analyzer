import sys
from PyQt5 import QtGui, QtWidgets, uic
from memdb import mem

class AppWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(AppWindow, self).__init__()
        uic.loadUi('app.ui', self)
        self.show()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = AppWindow()
    sys.exit(app.exec_())