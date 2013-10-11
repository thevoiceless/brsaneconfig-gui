#! /usr/bin/env python

import sys
from PyQt4 import QtGui


class ConfigWindow(QtGui.QWidget):

    def __init__(self):
        # The super() method returns the parent object of the given class
        super(ConfigWindow, self).__init__()
        self.initUI()

    def initUI(self):
        # setGeometry(x, y, width, height) sets window location and size
        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('brsaneconfig3')
        self.show()


def main():

    # Every PyQt4 application must create an application object
    app = QtGui.QApplication(sys.argv)

    window = ConfigWindow()

    # Because 'exec' is a Python keyword, 'exec_' was used instead
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()