#! /usr/bin/env python

import sys
import subprocess
from PyQt4 import QtGui


DEBUG = True
WINDOW_TITLE = 'brsaneconfig3 GUI'


class ConfigWindow(QtGui.QWidget):
    ID = 0
    NAME = 1
    MODEL = 2
    IP = 3
    HEADER = "Devices on network"

    def __init__(self):
        # The super() method returns the parent object of the given class
        super(ConfigWindow, self).__init__()

        self.supportedModels = []
        self.myPrinters = []

        self.gatherInfo()
        self.initUI()

    def gatherInfo(self):
        output = subprocess.check_output(["brsaneconfig3", "-q"]).splitlines()

        # Get index of the header that separates the list of supported models from the user's devices
        headerLoc = output.index(ConfigWindow.HEADER)

        # Strip out blank lines from list of models
        modelNames = [item for item in output[0:headerLoc] if len(item) > 0]
        # Don't include the header in the user's devices
        myPrintersInfo = output[headerLoc + 1:]

        # Populate self.supportedModels
        for model in modelNames:
            try:
                num, name = model.split()
                print num, name
                # Remove surrounding quotation marks
                self.supportedModels.append(name.replace('"', ''))
            except:
                print "Ignoring model {}, no model name given".format(num)
                continue

        # Populate self.myPrinters
        for printerInfo in myPrintersInfo:
            num, friendlyName, modelName, ip = printerInfo.split()
            # Remove surrounding quotation marks and the 'I:' prefix
            self.myPrinters.append([num, friendlyName, modelName.replace('"', ''), ip.replace("I:", '')])

        print self.supportedModels
        print self.myPrinters

    def initUI(self):
        self.resize(250, 250)
        self.setWindowTitle(WINDOW_TITLE)
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