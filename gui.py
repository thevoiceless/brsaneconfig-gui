#! /usr/bin/env python

import sys
import subprocess
from PyQt4 import QtGui


DEBUG = True
WINDOW_TITLE = 'brsaneconfig3 GUI'
WIDTH_FUDGE = 30

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

        # TODO: Populate form based on selected device
        print "Default selected device is \"" + self.deviceList.currentItem().text() + "\""

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

        # Populate self.myPrinters
        for printerInfo in myPrintersInfo:
            num, friendlyName, modelName, ipOrNode = printerInfo.split()
            # Check if IP or node name is specified
            isNode = ipOrNode.startswith("I:")
            # Remove surrounding quotation marks and the 'I:' prefix
            self.myPrinters.append([num, friendlyName, modelName.replace('"', ''), ipOrNode.replace("I:", ''), isNode])

        self.deviceList.addItems([printer[ConfigWindow.NAME] for printer in self.myPrinters])
        self.deviceList.setCurrentRow(0)

    def initUI(self):
        # Device list on left
        deviceListPanel = QtGui.QVBoxLayout()
        deviceListPanel.addWidget(self.deviceList)
        addDeviceBtn = QtGui.QPushButton("Add New Device")
        deviceListPanel.addWidget(addDeviceBtn)

        # Main layout
        mainHBox = QtGui.QHBoxLayout()
        mainHBox.addLayout(deviceListPanel)
        mainWidget = QtGui.QWidget()
        mainWidget.setLayout(mainHBox)
        self.setCentralWidget(mainWidget)
        # Do not allow resizing the devices list
        self.deviceList.setMaximumWidth(self.deviceList.sizeHintForColumn(0) + WIDTH_FUDGE)
        self.deviceList.setMinimumWidth(addDeviceBtn.minimumSizeHint().width())

        # Friendly name, user input
        friendlyName = QtGui.QLabel('Name:')
        # TODO: Disallow whitespace
        friendlyNameEdit = QtGui.QLineEdit()

        # Model name, combo box
        modelName = QtGui.QLabel('Model:')
        modelNameSelect = QtGui.QComboBox()
        modelNameSelect.addItems(self.supportedModels)
        # http://stackoverflow.com/a/11254459/1693087
        # Apply stylesheet to allow limiting max number of items
        modelNameSelect.setStyleSheet("QComboBox { combobox-popup: 0; }")
        modelNameSelect.setMaxVisibleItems(10)

        # IP address or node name, radio buttons
        group = QtGui.QButtonGroup()
        ipRadio = QtGui.QRadioButton("IP:")
        nodeRadio = QtGui.QRadioButton("Node:")
        group.addButton(ipRadio)
        group.addButton(nodeRadio)
        group.setExclusive(True)

        ipEdit = QtGui.QLineEdit()
        ipEdit.setInputMask("999.999.999.999; ")
        nodePrefix = QtGui.QLabel("BRN_")
        nodeEdit = QtGui.QLineEdit()

        nodeNameLayout = QtGui.QHBoxLayout()
        nodeNameLayout.setSpacing(0)
        nodeNameLayout.addWidget(nodePrefix)
        nodeNameLayout.addWidget(nodeEdit)
        nodeNameWidget = QtGui.QWidget()
        nodeNameWidget.setLayout(nodeNameLayout)
        nodeNameWidget.setContentsMargins(0, 0, 0, 0)
        nodeNameWidget.layout().setContentsMargins(0, 0, 0, 0)

        # "Save" and "delete" buttons
        saveButton = QtGui.QPushButton("Save")
        deleteButton = QtGui.QPushButton("Delete")

        buttonsLayout = QtGui.QHBoxLayout()
        buttonsLayout.addWidget(deleteButton)
        buttonsLayout.addWidget(saveButton)
        buttonsWidget = QtGui.QWidget()
        buttonsWidget.setLayout(buttonsLayout)
        buttonsWidget.setContentsMargins(0, 0, 0, 0)
        buttonsWidget.layout().setContentsMargins(0, 0, 0, 0)

        # Device info to the right of the device list
        grid = QtGui.QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(friendlyName, 0, 0)
        grid.addWidget(friendlyNameEdit, 0, 1)

        grid.addWidget(modelName, 1, 0)
        grid.addWidget(modelNameSelect, 1, 1)

        grid.addWidget(ipRadio, 2, 0)
        grid.addWidget(ipEdit, 2, 1)
        grid.addWidget(nodeRadio, 3, 0)
        grid.addWidget(nodeNameWidget, 3, 1)

        grid.setRowStretch(4, 1)
        grid.addWidget(buttonsWidget, 5, 0, 1, 2)

        mainHBox.addLayout(grid)

        self.resize(450, self.minimumHeight())
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