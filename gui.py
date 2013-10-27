#! /usr/bin/env python

import sys
import subprocess
from PyQt4 import QtGui, QtCore


DEBUG = True
WINDOW_TITLE = 'brsaneconfig3'
WIDTH_FUDGE = 30


class BrotherDevice:
    def __init__(self, info):
        # Parse info
        num, friendlyName, modelName, ipOrNode = info.split()
        # Check if IP or node name is specified
        self.usesIP = ipOrNode.startswith("I:")
        self.devID = num
        self.name = friendlyName
        # Remove quotation marks surrounding the model name
        self.model = modelName.replace('"', '')
        # Remove prefixes
        self.addr = ipOrNode.replace("I:", '').replace("N:BRN_", "")

    def __str__(self):
        return "devID: {}, name: {}, model: {}, addr: {} ({})".format(self.devID,
                                                                      self.name,
                                                                      self.model,
                                                                      self.addr,
                                                                      'IP' if self.usesIP else 'node')


class ConfigWindow(QtGui.QMainWindow):
    HEADER = "Devices on network"

    def __init__(self):
        # The super() method returns the parent object of the given class
        super(ConfigWindow, self).__init__()

        self.supportedModels = []
        self.myDevices = []
        self.selectedDevice = []
        self.noWhitespaceRegex = QtCore.QRegExp('[^\s]+')
        self.hasEditedCurrentDevice = False

        # Interface elements
        self.deviceList = QtGui.QListWidget()
        self.friendlyNameEdit = QtGui.QLineEdit()
        self.modelNameSelect = QtGui.QComboBox()
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
        myDevicesInfo = output[headerLoc + 1:]

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
        for deviceInfo in myDevicesInfo:
            device = BrotherDevice(deviceInfo)
            self.myDevices.append(device)

        # self.deviceList contains only the names from self.myDevices
        self.deviceList.addItems([d.name for d in self.myDevices])
        self.deviceList.setCurrentRow(0)

    def initUI(self):
        # TODO: Possibly separate each block of code into its own function
        # Device list on left
        deviceListPanel = QtGui.QVBoxLayout()
        deviceListPanel.addWidget(self.deviceList)
        addDeviceBtn = QtGui.QPushButton("Add New Device")
        deviceListPanel.addWidget(addDeviceBtn)
        self.deviceList.currentRowChanged.connect(self.onSelectedDeviceChange)

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
        self.modelNameSelect.addItems(self.supportedModels)
        # http://stackoverflow.com/a/11254459/1693087
        # Apply stylesheet to allow limiting max number of items
        self.modelNameSelect.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.modelNameSelect.setMaxVisibleItems(10)
        self.modelNameSelect.currentIndexChanged.connect(self.onModelNameChange)

        # IP address or node name, radio buttons
        group = QtGui.QButtonGroup()
        self.ipRadio = QtGui.QRadioButton("IP:")
        self.nodeRadio = QtGui.QRadioButton("Node:")
        group.addButton(self.ipRadio)
        group.addButton(self.nodeRadio)
        group.setExclusive(True)

        # IP address, split into four 3-digit sections
        ipSegmentValidator = QtGui.QIntValidator(001, 999)
        ipEdit1 = QtGui.QLineEdit()
        ipEdit2 = QtGui.QLineEdit()
        ipEdit3 = QtGui.QLineEdit()
        ipEdit4 = QtGui.QLineEdit()
        self.ipEdits = [ipEdit1, ipEdit2, ipEdit3, ipEdit4]
        ipLayout = QtGui.QHBoxLayout()
        ipLayout.setSpacing(0)

        for i in range(4):
            self.ipEdits[i].setValidator(ipSegmentValidator)
            self.ipEdits[i].setMaxLength(3)
            self.ipEdits[i].setAlignment(QtCore.Qt.AlignCenter)
            ipLayout.addWidget(self.ipEdits[i])
            if i != 3:
                ipLayout.addWidget(QtGui.QLabel("."))

        self.ipWidget = QtGui.QWidget()
        self.ipWidget.setLayout(ipLayout)
        self.ipWidget.setContentsMargins(0, 0, 0, 0)
        self.ipWidget.layout().setContentsMargins(0, 0, 0, 0)

        # Node name, user does not need to worry about the "BRN_" prefix
        nodePrefix = QtGui.QLabel("BRN_")
        self.nodeEdit = QtGui.QLineEdit()
        nodeNameLayout = QtGui.QHBoxLayout()
        nodeNameLayout.setSpacing(0)
        nodeNameLayout.addWidget(nodePrefix)
        nodeNameLayout.addWidget(self.nodeEdit)
        self.nodeNameWidget = QtGui.QWidget()
        self.nodeNameWidget.setLayout(nodeNameLayout)
        self.nodeNameWidget.setContentsMargins(0, 0, 0, 0)
        self.nodeNameWidget.layout().setContentsMargins(0, 0, 0, 0)

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
        grid.addWidget(self.modelNameSelect, 1, 1)

        grid.addWidget(self.ipRadio, 2, 0)
        grid.addWidget(self.ipWidget, 2, 1)
        grid.addWidget(self.nodeRadio, 3, 0)
        grid.addWidget(self.nodeNameWidget, 3, 1)

        grid.setRowStretch(4, 1)
        grid.addWidget(buttonsWidget, 5, 0, 1, 2)

        mainHBox.addLayout(grid)

        # Get info about currently-selected device and populate fields
        self.selectedDevice = self.myDevices[self.deviceList.currentRow()]
        self.updateFields()
        print "Initially selected device is", self.selectedDevice

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

    def updateFields(self):
        self.friendlyNameEdit.setText(self.selectedDevice.name)

        # Set content of model name dropdown
        self.modelNameSelect.setCurrentIndex(self.modelNameSelect.findText(self.selectedDevice.model))

        # Populate IP or node name
        if self.selectedDevice.usesIP:
            self.ipRadio.setChecked(True)
            for textbox, segment in zip(self.ipEdits, self.selectedDevice.addr.split('.')):
                textbox.setText(segment)
            self.nodeNameWidget.setEnabled(False)
        else:
            self.nodeRadio.setChecked(True)
            print "addr", self.selectedDevice.addr
            self.nodeEdit.setText(self.selectedDevice.addr)
            self.ipWidget.setEnabled(False)

    # React when self.friendlyNameEdit changes
    def onNameInputChange(self):
        # Disallow whitespace
        if not self.noWhitespaceRegex.exactMatch(self.friendlyNameEdit.text()) and len(self.friendlyNameEdit.text()) > 0:
            QtGui.QMessageBox.warning(None, "Error", "The name cannot contain whitespace.")
            self.friendlyNameEdit.setText(self.friendlyNameEdit.text()[:-1])
        # Check if modified from original
        if self.friendlyNameEdit.text() != self.selectedDevice.name:
            self.hasEditedCurrentDevice = True
            self.saveBtn.setEnabled(True)
        else:
            self.hasEditedCurrentDevice = False
            self.saveBtn.setEnabled(False)

    # React when self.modelNameSelect changes
    def onModelNameChange(self):
        selectedModel = self.modelNameSelect.currentText()
        if selectedModel != self.selectedDevice.model:
            self.hasEditedCurrentDevice = True
            self.saveBtn.setEnabled(True)
        else:
            self.hasEditedCurrentDevice = False
            self.saveBtn.setEnabled(False)

    # React when a different device is selected in self.deviceList
    def onSelectedDeviceChange(self, row):
        print "Selected row is now", row
        print "Device at that index is", self.myDevices[row]
        print "row", row


def main():
    # Every PyQt4 application must create an application object
    app = QtGui.QApplication(sys.argv)

    window = ConfigWindow()

    # Because 'exec' is a Python keyword, 'exec_' was used instead
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()