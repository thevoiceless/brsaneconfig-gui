#! /usr/bin/env python

import sys
import subprocess
from PyQt4 import QtGui, QtCore


DEBUG = True
WINDOW_TITLE = 'brsaneconfig3'
WIDTH_FUDGE = 30


class ConfigWindow(QtGui.QMainWindow):
    ID = 0
    NAME = 1
    MODEL = 2
    ADDR = 3
    USES_IP = 4
    HEADER = "Devices on network"
    PREFIX = "BRN_"

    def __init__(self):
        # The super() method returns the parent object of the given class
        super(ConfigWindow, self).__init__()

        self.supportedModels = []
        self.myDevices = []
        self.selectedDevice = []

        self.deviceList = QtGui.QListWidget()
        self.noWhitespaceRegex = QtCore.QRegExp('[^\s]+')
        self.friendlyNameEdit = QtGui.QLineEdit()
        self.hasEditedCurrentDevice = False
        self.saveBtn = None

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

        # Populate self.myDevices
        for printerInfo in myPrintersInfo:
            num, friendlyName, modelName, ipOrNode = printerInfo.split()
            # Check if IP or node name is specified
            usesIP = ipOrNode.startswith("I:")
            # Remove surrounding quotation marks and the 'I:' prefix
            self.myDevices.append([num,
                                   friendlyName,
                                   modelName.replace('"', ''),
                                   ipOrNode.replace("I:", '').replace("N:", ""),
                                   usesIP])

        # self.deviceList contains only the names from self.myDevices
        self.deviceList.addItems([device[ConfigWindow.NAME] for device in self.myDevices])
        self.deviceList.setCurrentRow(0)

    def initUI(self):
        # TODO: Possibly separate each block of code into its own function
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
        # Verify text as it is typed so that we can display a message
        self.friendlyNameEdit.textEdited.connect(self.onNameInputChange)

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

        # IP address, split into four 3-digit sections
        ipSegmentValidator = QtGui.QIntValidator(001, 999)
        ipEdit1 = QtGui.QLineEdit()
        ipEdit2 = QtGui.QLineEdit()
        ipEdit3 = QtGui.QLineEdit()
        ipEdit4 = QtGui.QLineEdit()
        ipEdits = [ipEdit1, ipEdit2, ipEdit3, ipEdit4]
        ipLayout = QtGui.QHBoxLayout()
        ipLayout.setSpacing(0)

        for i in range(4):
            ipEdits[i].setValidator(ipSegmentValidator)
            ipEdits[i].setMaxLength(3)
            ipEdits[i].setAlignment(QtCore.Qt.AlignCenter)
            ipLayout.addWidget(ipEdits[i])
            if i != 3:
                ipLayout.addWidget(QtGui.QLabel("."))

        ipWidget = QtGui.QWidget()
        ipWidget.setLayout(ipLayout)
        ipWidget.setContentsMargins(0, 0, 0, 0)
        ipWidget.layout().setContentsMargins(0, 0, 0, 0)

        # Node name, prefixed with ConfigWindow.PREFIX
        nodePrefix = QtGui.QLabel(ConfigWindow.PREFIX)
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
        self.saveBtn = QtGui.QPushButton("Save")
        self.saveBtn.setEnabled(False)
        deleteButton = QtGui.QPushButton("Delete")

        buttonsLayout = QtGui.QHBoxLayout()
        buttonsLayout.addWidget(deleteButton)
        buttonsLayout.addWidget(self.saveBtn)
        buttonsWidget = QtGui.QWidget()
        buttonsWidget.setLayout(buttonsLayout)
        buttonsWidget.setContentsMargins(0, 0, 0, 0)
        buttonsWidget.layout().setContentsMargins(0, 0, 0, 0)

        # Info for the selected device is displayed to the right of the device list
        grid = QtGui.QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(friendlyName, 0, 0)
        grid.addWidget(self.friendlyNameEdit, 0, 1)

        grid.addWidget(modelName, 1, 0)
        grid.addWidget(modelNameSelect, 1, 1)

        grid.addWidget(ipRadio, 2, 0)
        grid.addWidget(ipWidget, 2, 1)
        grid.addWidget(nodeRadio, 3, 0)
        grid.addWidget(nodeNameWidget, 3, 1)

        grid.setRowStretch(4, 1)
        grid.addWidget(buttonsWidget, 5, 0, 1, 2)

        mainHBox.addLayout(grid)

        # Get info about currently-selected device and populate fields
        selectedName = self.deviceList.currentItem().text()
        self.friendlyNameEdit.setText(selectedName)

        for device in self.myDevices:
            if device[ConfigWindow.NAME] == selectedName:
                self.selectedDevice = device
                print "Selected device is", self.selectedDevice
                break

        modelNameSelect.setCurrentIndex(modelNameSelect.findText(self.selectedDevice[ConfigWindow.MODEL]))

        if self.selectedDevice[ConfigWindow.USES_IP]:
            ipRadio.setChecked(True)
            for textbox, segment in zip(ipEdits, self.selectedDevice[ConfigWindow.ADDR].split('.')):
                textbox.setText(segment)
            nodeNameWidget.setEnabled(False)
        else:
            nodeRadio.setChecked(True)
            addr = self.selectedDevice[ConfigWindow.ADDR]
            print "addr", addr
            nodeEdit.setText(addr.replace(ConfigWindow.PREFIX, "", 1))
            ipWidget.setEnabled(False)

        # Resize and show
        self.resize(self.minimumSizeHint().width(), self.minimumSizeHint().height())
        self.setWindowTitle(WINDOW_TITLE)
        self.center()
        self.show()

    # Center the window on the screen
    def center(self):
        ourRect = self.frameGeometry()
        screenCenter = QtGui.QDesktopWidget().availableGeometry().center()
        ourRect.moveCenter(screenCenter)
        self.move(ourRect.topLeft())

    # Error-checking when self.friendlyNameEdit changes
    def onNameInputChange(self):
        # Disallow whitespace
        if not self.noWhitespaceRegex.exactMatch(self.friendlyNameEdit.text()) and len(self.friendlyNameEdit.text()) > 0:
            QtGui.QMessageBox.warning(None, "Error", "The name cannot contain whitespace.")
            self.friendlyNameEdit.setText(self.friendlyNameEdit.text()[:-1])
        # Check if modified from original
        if self.friendlyNameEdit.text() != self.selectedDevice[ConfigWindow.NAME]:
            self.hasEditedCurrentDevice = True
            self.saveBtn.setEnabled(True)
        else:
            self.hasEditedCurrentDevice = False
            self.saveBtn.setEnabled(False)


def main():
    # Every PyQt4 application must create an application object
    app = QtGui.QApplication(sys.argv)

    window = ConfigWindow()

    # Because 'exec' is a Python keyword, 'exec_' was used instead
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()