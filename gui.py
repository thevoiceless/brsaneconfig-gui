#! /usr/bin/env python

import sys, subprocess
from PyQt4 import QtGui, QtCore


DEBUG = True
WINDOW_TITLE = 'brsaneconfig3'
WIDTH_FUDGE = 30


class BrotherDevice:
    def __init__(self, info = None):
        if info is not None:
            self.isNew = False
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
        else:
            self.isNew = True
            self.devID = -1
            self.name = ''
            self.model = ''
            self.usesIP = True
            self.addr = '...'

    def __str__(self):
        return "devID: {}, name: {}, model: {}, addr: {} ({})".format(self.devID, self.name, self.model, self.addr,
                                                                      'IP' if self.usesIP else 'node')

    @staticmethod
    def queryDevices():
        try:
            output = subprocess.check_output(["brsaneconfig3", "-q"])
            # brsaneconfig3 does not return nonzero exit code even when given bad params, prints usage text instead
            if "USAGE" in output:
                raise RuntimeError("Invalid output when querying devices.")
            return output.splitlines()
        except RuntimeError as e:
            QtGui.QMessageBox.critical(None, "Error", e.message)
            sys.exit(1)
        # The rest of these exceptions are what *should* be raised
        except subprocess.CalledProcessError as e:
            QtGui.QMessageBox.critical(None, "Error", "Could not gather list of devices.\n" + e.output)
            sys.exit(e.returncode)
        except OSError as e:
            QtGui.QMessageBox.critical(None, "Error", "Invalid command.\n" + e.strerror)
            sys.exit(e.errno)
        except ValueError as e:
            QtGui.QMessageBox.critical(None, "Error", "Invalid arguments passed to Popen.")
            sys.exit(1)

    @staticmethod
    def addDevice(device):
        try:
            output = subprocess.check_output(["brsaneconfig3", "-a",
                                              "name={}".format(device.name),
                                              "model={}".format(device.model),
                                              "ip={}".format(device.addr) if device.usesIP else "nodename=BRN_{}".format(device.addr)])
            # There should be no output (see comments in queryDevices())
            if len(output) > 0:
                raise RuntimeError("Error adding device.")
            return output
        except RuntimeError as e:
            QtGui.QMessageBox.critical(None, "Error", e.message)
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            QtGui.QMessageBox.critical(None, "Error", "Could not add device.\n" + e.output)
            sys.exit(e.returncode)
        except OSError as e:
            QtGui.QMessageBox.critical(None, "Error", "Invalid command.\n" + e.strerror)
            sys.exit(e.errno)
        except ValueError as e:
            QtGui.QMessageBox.critical(None, "Error", "Invalid arguments passed to Popen.")
            sys.exit(1)

    @staticmethod
    def removeDevice(name):
        try:
            output = subprocess.check_output(["brsaneconfig3", "-r", name])
            # There should be no output (see comments in queryDevices())
            if len(output) > 0:
                raise RuntimeError("Error removing device.")
            return output
        except RuntimeError as e:
            QtGui.QMessageBox.critical(None, "Error", e.message)
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            QtGui.QMessageBox.critical(None, "Error", "Could not remove device.\n" + e.output)
            sys.exit(e.returncode)
        except OSError as e:
            QtGui.QMessageBox.critical(None, "Error", "Invalid command.\n" + e.strerror)
            sys.exit(e.errno)
        except ValueError as e:
            QtGui.QMessageBox.critical(None, "Error", "Invalid arguments passed to Popen.")
            sys.exit(1)


class ConfigWindow(QtGui.QMainWindow):
    HEADER = "Devices on network"

    def __init__(self):
        # The super() method returns the parent object of the given class
        super(ConfigWindow, self).__init__()

        # Data structures and variables
        self.supportedModels = []
        self.myDevices = []
        self.currentDevice = []
        self.noWhitespaceRegex = QtCore.QRegExp('[^\s]+')
        self.hasEditedCurrentDevice = False
        self.ipEdits = []

        # Interface elements
        self.deviceList = QtGui.QListWidget()
        self.friendlyNameEdit = QtGui.QLineEdit()
        self.modelNameSelect = QtGui.QComboBox()
        self.saveBtn = QtGui.QPushButton("Save")
        self.deleteButton = QtGui.QPushButton("Delete")
        self.ipRadio = QtGui.QRadioButton("IP:")
        self.nodeRadio = QtGui.QRadioButton("Node:")
        self.ipWidget = QtGui.QWidget()
        self.nodeEdit = QtGui.QLineEdit()
        self.nodeNameWidget = QtGui.QWidget()

        self.gatherInfo()
        self.initUI()

    def gatherInfo(self):
        output = BrotherDevice.queryDevices()

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
            except ValueError:
                #print "Ignoring model {}, no model name given".format(num)
                continue
        self.supportedModels.sort()

        # Populate self.myDevices
        for deviceInfo in myDevicesInfo:
            device = BrotherDevice(deviceInfo)
            self.myDevices.append(device)

        # self.deviceList contains only the names from self.myDevices
        # TODO: What if there are no devices?
        self.deviceList.addItems([d.name for d in self.myDevices])
        self.deviceList.setCurrentRow(0)

    def initUI(self):
        # TODO: Possibly separate each block of code into its own function
        # Device list on left
        deviceListPanel = QtGui.QVBoxLayout()
        deviceListPanel.addWidget(self.deviceList)
        # TODO: Attach action, possibly pre-populate name
        addDeviceBtn = QtGui.QPushButton("Add New Device")
        deviceListPanel.addWidget(addDeviceBtn)
        self.deviceList.currentItemChanged.connect(self.onSelectedDeviceChange)
        addDeviceBtn.clicked.connect(self.addNewDevice)

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
        group.addButton(self.ipRadio)
        group.addButton(self.nodeRadio)
        group.setExclusive(True)
        self.ipRadio.toggled.connect(self.onRadioToggle)
        self.nodeRadio.toggled.connect(self.onRadioToggle)

        # IP address, split into four 3-digit sections
        ipSegmentValidator = QtGui.QIntValidator(001, 999)
        ipEdit1 = QtGui.QLineEdit()
        ipEdit2 = QtGui.QLineEdit()
        ipEdit3 = QtGui.QLineEdit()
        ipEdit4 = QtGui.QLineEdit()
        self.ipEdits = [ipEdit1, ipEdit2, ipEdit3, ipEdit4]
        ipLayout = QtGui.QHBoxLayout()
        ipLayout.setSpacing(0)

        # Only allow 3 digits in each part of the IP
        for i, textbox in enumerate(self.ipEdits):
            textbox.setValidator(ipSegmentValidator)
            textbox.setMaxLength(3)
            textbox.setAlignment(QtCore.Qt.AlignCenter)
            textbox.textEdited.connect(self.onIPChange)
            if i > 0:
                ipLayout.addWidget(QtGui.QLabel("."))
            ipLayout.addWidget(self.ipEdits[i])

        self.ipWidget.setLayout(ipLayout)
        self.ipWidget.setContentsMargins(0, 0, 0, 0)
        self.ipWidget.layout().setContentsMargins(0, 0, 0, 0)

        # Node name, user does not need to worry about the "BRN_" prefix
        nodePrefix = QtGui.QLabel("BRN_")
        nodeNameLayout = QtGui.QHBoxLayout()
        nodeNameLayout.setSpacing(0)
        nodeNameLayout.addWidget(nodePrefix)
        nodeNameLayout.addWidget(self.nodeEdit)
        self.nodeNameWidget = QtGui.QWidget()
        self.nodeNameWidget.setLayout(nodeNameLayout)
        self.nodeNameWidget.setContentsMargins(0, 0, 0, 0)
        self.nodeNameWidget.layout().setContentsMargins(0, 0, 0, 0)
        self.nodeEdit.textEdited.connect(self.onNodeChange)

        # "Save" and "delete" buttons
        self.saveBtn.setEnabled(False)
        self.saveBtn.clicked.connect(self.saveCurrentDevice)
        self.deleteButton.clicked.connect(self.deleteCurrentDevice)

        buttonsLayout = QtGui.QHBoxLayout()
        buttonsLayout.addWidget(self.deleteButton)
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
        self.currentDevice = self.myDevices[self.deviceList.currentRow()]
        self.updateFields()
        print "Initially selected device is", self.currentDevice

        # Resize and show
        self.resize(self.minimumSizeHint().width(), self.minimumSizeHint().height())
        self.setWindowTitle(WINDOW_TITLE)
        self.center()
        self.show()

        print "edited:", self.hasEditedCurrentDevice

    # Center the window on the screen
    def center(self):
        ourRect = self.frameGeometry()
        screenCenter = QtGui.QDesktopWidget().availableGeometry().center()
        ourRect.moveCenter(screenCenter)
        self.move(ourRect.topLeft())

    # Update fields in GUI based on current device
    def updateFields(self):
        self.friendlyNameEdit.setText(self.currentDevice.name)

        # Set content of model name dropdown
        self.modelNameSelect.setCurrentIndex(self.modelNameSelect.findText(self.currentDevice.model))

        # Populate IP or node name
        # Populate text boxes before setting radio button as doing so triggers the "toggled" signal and checks for edits
        if self.currentDevice.usesIP:
            self.ipWidget.setEnabled(True)
            for textbox, segment in zip(self.ipEdits, self.currentDevice.addr.split('.')):
                textbox.setText(segment)
            self.ipRadio.setChecked(True)
            self.nodeNameWidget.setEnabled(False)
            self.nodeEdit.setText("")
        else:
            self.nodeNameWidget.setEnabled(True)
            self.nodeEdit.setText(self.currentDevice.addr)
            self.nodeRadio.setChecked(True)
            self.ipWidget.setEnabled(False)
            for textbox in self.ipEdits:
                textbox.setText("")

    # Join the IP address components together
    def getIP(self):
        ip = ''
        for i, textbox in enumerate(self.ipEdits):
            if i > 0:
                ip += "."
            ip += textbox.text().rightJustified(3, QtCore.QChar('0'))
        return ip

    # If the params are not equal, the current device has been edited
    def hasEditedIfNotEqual(self, thing1, thing2):
        if thing1 != thing2:
            self.hasEditedCurrentDevice = True
            self.saveBtn.setEnabled(True)
        else:
            self.hasEditedCurrentDevice = False
            self.saveBtn.setEnabled(False)

    # Create a new device
    def addNewDevice(self):
        newDevice = BrotherDevice()
        print newDevice
        self.myDevices.append(newDevice)
        self.deviceList.addItem('New Device')
        self.onSelectedDeviceChange(self.deviceList.item(len(self.myDevices) - 1), self.deviceList.currentItem())
        self.deviceList.setCurrentRow(len(self.myDevices) - 1)
        self.friendlyNameEdit.setFocus()

    # Common save operations
    # TODO: Don't save if the name is empty or a duplicate
    def saveHelper(self):
        BrotherDevice.removeDevice(self.currentDevice.name)
        self.updateCurrentDevice()
        BrotherDevice.addDevice(self.currentDevice)
        self.currentDevice.isNew = False
        self.hasEditedCurrentDevice = False
        self.saveBtn.setEnabled(False)

    # Save device
    # Apparently changing the data backing the QListWidget isn't enough, must manually update the label
    def saveCurrentDevice(self):
        self.saveHelper()
        self.deviceList.currentItem().setText(self.currentDevice.name)

    # Delete device
    def deleteCurrentDevice(self):
        print "delete device", self.currentDevice
        print "row", self.deviceList.currentRow()
        print "at that index in myDevices:", self.myDevices[self.deviceList.currentRow()]
        BrotherDevice.removeDevice(self.currentDevice.name)
        del self.myDevices[self.deviceList.currentRow()]
        self.deviceList.takeItem(self.deviceList.currentRow())
        self.hasEditedCurrentDevice = False
        self.onSelectedDeviceChange(None, None)

    # React when a different device is selected in self.deviceList
    def onSelectedDeviceChange(self, currentItem, previousItem):
        if self.hasEditedCurrentDevice:
            saveChanges = QtGui.QMessageBox.question(None, "", "Save changes to current device?",
                                                     QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
            if saveChanges == QtGui.QMessageBox.Yes:
                self.saveHelper()
                previousItem.setText(self.currentDevice.name)
            else:
                if self.currentDevice.isNew:
                    self.deviceList.takeItem(self.deviceList.row(previousItem))
                    self.myDevices.pop()

        row = self.deviceList.currentRow()
        self.currentDevice = self.myDevices[row]
        self.updateFields()
        print "Device at row {} is {}".format(row, self.myDevices[row])

    # React when self.friendlyNameEdit changes
    def onNameInputChange(self):
        # Disallow whitespace
        if not self.noWhitespaceRegex.exactMatch(self.friendlyNameEdit.text()) and len(self.friendlyNameEdit.text()) > 0:
            QtGui.QMessageBox.warning(None, "Error", "The name cannot contain whitespace.")
            self.friendlyNameEdit.setText(self.friendlyNameEdit.text()[:-1])
        # Check if modified from original
        self.hasEditedIfNotEqual(self.friendlyNameEdit.text(), self.currentDevice.name)

    # React when self.modelNameSelect changes
    def onModelNameChange(self):
        selectedModel = self.modelNameSelect.currentText()
        self.hasEditedIfNotEqual(selectedModel, self.currentDevice.model)

    # React when address type changes
    def onRadioToggle(self, isChecked):
        if self.ipRadio.isChecked():
            if not self.currentDevice.usesIP:
                self.hasEditedCurrentDevice = True
                self.saveBtn.setEnabled(True)
            else:
                self.hasEditedCurrentDevice = False
                self.saveBtn.setEnabled(False)
                self.hasEditedIfNotEqual(self.getIP(), self.currentDevice.addr)
            self.ipWidget.setEnabled(True)
            self.nodeNameWidget.setEnabled(False)
        elif self.nodeRadio.isChecked():
            if self.currentDevice.usesIP:
                self.hasEditedCurrentDevice = True
                self.saveBtn.setEnabled(True)
            else:
                self.hasEditedCurrentDevice = False
                self.saveBtn.setEnabled(False)
                self.hasEditedIfNotEqual(self.nodeEdit.text(), self.currentDevice.addr)
            self.ipWidget.setEnabled(False)
            self.nodeNameWidget.setEnabled(True)
        else:
            self.hasEditedCurrentDevice = False
            self.saveBtn.setEnabled(False)

    # React when IP address changes
    def onIPChange(self):
        self.hasEditedIfNotEqual(self.getIP(), self.currentDevice.addr)

    # React to node name changes
    def onNodeChange(self):
        # Disallow whitespace
        if not self.noWhitespaceRegex.exactMatch(self.nodeEdit.text()) and len(self.nodeEdit.text()) > 0:
            QtGui.QMessageBox.warning(None, "Error", "The node name cannot contain whitespace.")
            self.nodeEdit.setText(self.nodeEdit.text()[:-1])
        self.hasEditedIfNotEqual(self.nodeEdit.text(), self.currentDevice.addr)

    # Update the properties of self.currentDevice based on the entered values
    def updateCurrentDevice(self):
        self.currentDevice.name = self.friendlyNameEdit.text()
        self.currentDevice.model = self.modelNameSelect.currentText()
        if self.ipRadio.isChecked():
            self.currentDevice.usesIP = True
            self.currentDevice.addr = self.getIP()
        else:
            self.currentDevice.usesIP = False
            self.currentDevice.addr = self.nodeEdit.text()


def main():
    # Every PyQt4 application must create an application object
    app = QtGui.QApplication(sys.argv)

    window = ConfigWindow()

    # Because 'exec' is a Python keyword, Qt uses 'exec_' instead
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()