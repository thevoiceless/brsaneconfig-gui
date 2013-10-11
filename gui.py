#! /usr/bin/env python

import sys
import subprocess
from PyQt4 import QtGui


DEBUG = True
WINDOW_TITLE = 'brsaneconfig3 GUI'
SCROLLBAR_FUDGE = 20

class ConfigWindow(QtGui.QMainWindow):
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
        self.deviceList = QtGui.QListWidget()

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

        # Populate self.supportedModels and set self.devicesList
        for model in modelNames:
            try:
                num, name = model.split()
                # Remove surrounding quotation marks
                self.supportedModels.append(name.replace('"', ''))
            except:
                #print "Ignoring model {}, no model name given".format(num)
                continue
        self.deviceList.addItems(self.supportedModels)

        # Populate self.myPrinters
        for printerInfo in myPrintersInfo:
            num, friendlyName, modelName, ip = printerInfo.split()
            # Remove surrounding quotation marks and the 'I:' prefix
            self.myPrinters.append([num, friendlyName, modelName.replace('"', ''), ip.replace("I:", '')])

        #self.deviceList.addItems([printer[ConfigWindow.NAME] for printer in self.myPrinters])

    def initUI(self):
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.deviceList)
        hbox.addStretch(1)
        widgt = QtGui.QWidget()
        widgt.setLayout(hbox)
        self.setCentralWidget(widgt)
        self.deviceList.setMaximumWidth(self.deviceList.sizeHintForColumn(0) + SCROLLBAR_FUDGE)

        self.resize(400, 250)
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