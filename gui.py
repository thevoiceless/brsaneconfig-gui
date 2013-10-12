#! /usr/bin/env python

import sys
import subprocess
from PyQt4 import QtGui


DEBUG = True
WINDOW_TITLE = 'brsaneconfig3 GUI'
SCROLLBAR_FUDGE = 30

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
        self.supportedModels.sort()
        self.deviceList.addItems(self.supportedModels)

        # Populate self.myPrinters
        for printerInfo in myPrintersInfo:
            num, friendlyName, modelName, ipOrNode = printerInfo.split()
            # Check if IP or node name is specified
            isNode = ipOrNode.startswith("I:")
            # Remove surrounding quotation marks and the 'I:' prefix
            self.myPrinters.append([num, friendlyName, modelName.replace('"', ''), ipOrNode.replace("I:", ''), isNode])

        #self.deviceList.addItems([printer[ConfigWindow.NAME] for printer in self.myPrinters])

    def initUI(self):
        # Device list on left
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.deviceList)
        vbox.addWidget(QtGui.QPushButton("Add New Device"))

        # Main layout
        hbox = QtGui.QHBoxLayout()
        hbox.addLayout(vbox)
        widgt = QtGui.QWidget()
        widgt.setLayout(hbox)
        self.setCentralWidget(widgt)
        # Do not allow resizing the devices list
        self.deviceList.setMaximumWidth(self.deviceList.sizeHintForColumn(0) + SCROLLBAR_FUDGE)
        self.deviceList.setMinimumWidth(self.deviceList.sizeHintForColumn(0) + SCROLLBAR_FUDGE)

        friendlyName = QtGui.QLabel('Name:')
        friendlyNameEdit = QtGui.QLineEdit()

        modelName = QtGui.QLabel('Model:')
        modelNameSelect = QtGui.QComboBox()
        modelNameSelect.addItems(self.supportedModels)
        # http://stackoverflow.com/a/11254459/1693087
        # Apply stylesheet to allow limiting max number of items
        modelNameSelect.setStyleSheet("QComboBox { combobox-popup: 0; }")
        modelNameSelect.setMaxVisibleItems(10)

        ipLabel = QtGui.QLabel('IP:')

        nodeLabel = QtGui.QLabel('Node:')

        grid = QtGui.QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(friendlyName, 1, 0)
        grid.addWidget(friendlyNameEdit, 1, 1)

        grid.addWidget(modelName, 2, 0)
        grid.addWidget(modelNameSelect, 2, 1)

        hbox.addLayout(grid)

        #hbox.addStretch(1)
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