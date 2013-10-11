#! /usr/bin/env python

import sys
import subprocess
from PyQt4 import QtGui


class ConfigWindow(QtGui.QWidget):
    ID = 0
    NAME = 1
    MODEL = 2
    IP = 3

    def __init__(self):
        # The super() method returns the parent object of the given class
        super(ConfigWindow, self).__init__()

        self.printers = []
        self.gatherInfo()
        self.initUI()

    def gatherInfo(self):
        output = subprocess.check_output(["brsaneconfig3", "-q"]).splitlines()
        relevantOutput = output[output.index('Devices on network') + 1:]

        for printerInfo in relevantOutput:
            id, friendlyName, modelName, ip = printerInfo.split()
            modelName = modelName.replace('"', '')
            ip = ip.replace("I:", '')
            self.printers.append([id, friendlyName, modelName, ip])

        print self.printers

    def initUI(self):
        # setGeometry(x, y, width, height) sets window location and size
        #self.setGeometry(300, 300, 250, 150)
        self.resize(250, 250)
        self.setWindowTitle('brsaneconfig3')
        self.center()
        self.show()

    def center(self):
        ourRect = self.frameGeometry()
        screenCenter = QtGui.QDesktopWidget().availableGeometry().center()
        ourRect.moveCenter(screenCenter)
        self.move(ourRect.topLeft())


def main():
    # Every PyQt4 application must create an application object
    app = QtGui.QApplication(sys.argv)

    window = ConfigWindow()

    # Because 'exec' is a Python keyword, 'exec_' was used instead
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()