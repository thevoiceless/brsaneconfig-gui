#! /usr/bin/env python

import sys, subprocess
from PyQt4 import QtGui, QtCore


DEBUG = True
debugcounter = 0
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
        self.allowOriginalName = False
        self.allowOriginalModel = False
        self.allowOriginalAddr = False

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
        self.previousItem = None

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
        addDeviceBtn = QtGui.QPushButton("Add New Device")
        deviceListPanel.addWidget(addDeviceBtn)
        # Connect to currentItemChanged to remember the previous seleted item
        self.deviceList.currentItemChanged.connect(self.rememberPreviousItem)
        # Do error-checking logic when item is clicked
        self.deviceList.itemPressed.connect(self.onDeviceClicked)
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
        # Disable signals until all fields have been populated
        print "disabling signals"
        self.disableSignals()
        print "setting name"
        self.friendlyNameEdit.setText(self.currentDevice.name)

        # Set content of model name dropdown
        print "setting model"
        self.modelNameSelect.setCurrentIndex(self.modelNameSelect.findText(self.currentDevice.model))

        # Populate IP or node name
        print "setting address"
        if self.currentDevice.usesIP:
            self.ipWidget.setEnabled(True)
            print "checking ip"
            self.ipRadio.setChecked(True)
            print "populating ip"
            for textbox, segment in zip(self.ipEdits, self.currentDevice.addr.split('.')):
                textbox.setText(segment)
            self.nodeNameWidget.setEnabled(False)
            self.nodeEdit.setText("")
        else:
            self.nodeNameWidget.setEnabled(True)
            print "checking node"
            self.nodeRadio.setChecked(True)
            print "populating node"
            self.nodeEdit.setText(self.currentDevice.addr)
            self.ipWidget.setEnabled(False)
            for textbox in self.ipEdits:
                textbox.setText("")

        print "enabling signals"
        self.enableSignals()

    # Join the IP address components together
    # Will return "000.000.000.000" if no IP is entered
    def getIP(self):
        ip = ''
        for i, textbox in enumerate(self.ipEdits):
            if i > 0:
                ip += "."
            ip += textbox.text().rightJustified(3, QtCore.QChar('0'))
        return ip

    # If the params are not equal, the current device has been edited
    # The allowOriginal parameter is used to override the comparison in some situations
    # For example, if the user makes multiple changes but only some of them are valid, overriding the comparison for
    # the invalid fields allows the user to enter the original values again. This usually happens if they leave a field
    # blank because the contents of empty fields are currently left empty after validation fails. As a result, the save
    # button would need to be enabled even if they enter the original value again.
    def hasEditedIfNotEqual(self, thing1, thing2, allowOriginal = False):
        return thing1 != thing2 or allowOriginal

    # Pressed the "Add Device" button
    def addNewDevice(self):
        # Create the new device and add it to myDevices and the devices list
        newDevice = BrotherDevice()
        self.myDevices.append(newDevice)
        self.deviceList.addItem('New Device')
        # TODO: Try to extract common dialog code
        # Check if there are changes we need to save
        if self.hasEditedCurrentDevice:
            saveChanges = QtGui.QMessageBox.question(None, "", "Save changes to current device?",
                                                     QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                     QtGui.QMessageBox.No)
            if saveChanges == QtGui.QMessageBox.Yes:
                # If the user wants to save changes, attempt to do so before switching to the new device
                if self.saveHelper():
                    print "save successful"
                    self.deviceList.currentItem().setText(self.currentDevice.name)
                # If the save operation fails, the user must fix things before they can switch to adding a new device
                else:
                    self.deviceList.takeItem(len(self.myDevices) - 1)
                    self.myDevices.pop()
                    return

        # If the save operation succeeds or if there are no changes to save, switch to the new device
        self.deviceList.setCurrentRow(len(self.myDevices) - 1)
        self.currentDevice = self.myDevices[self.deviceList.currentRow()]
        self.hasEditedCurrentDevice = True
        print 'EDITED SET TO TRUE in addDevice'
        self.updateFields()
        self.friendlyNameEdit.setFocus()

    # Common save operation (does not update name displayed in device list)
    def saveHelper(self):
        # Stop here if input is invalid
        print "validating input"
        if not self.validateFieldValues():
            return False
        # Only remove device if it has already been saved
        if not self.currentDevice.isNew:
            print "removing '%s'" % self.currentDevice.name
            BrotherDevice.removeDevice(self.currentDevice.name)
        # Save changes
        self.updateCurrentDevice()
        print "saving"
        BrotherDevice.addDevice(self.currentDevice)
        # Reset flags
        self.currentDevice.isNew = False
        self.hasEditedCurrentDevice = False
        self.saveBtn.setEnabled(False)
        self.resetValidationExceptions()
        return True

    # Save device and update the displayed name
    def saveCurrentDevice(self):
        if self.saveHelper():
            # Apparently changing the data backing the QListWidget isn't enough, must manually update the label
            self.deviceList.currentItem().setText(self.currentDevice.name)

    # Delete device
    def deleteCurrentDevice(self):
        areYouSure = QtGui.QMessageBox.question(None, "", "Delete '{}'?".format(self.currentDevice.name),
                                                         QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                         QtGui.QMessageBox.No)
        if areYouSure == QtGui.QMessageBox.Yes:
            print "delete device", self.currentDevice
            print "row", self.deviceList.currentRow()
            print "at that index in myDevices:", self.myDevices[self.deviceList.currentRow()]
            BrotherDevice.removeDevice(self.currentDevice.name)
            del self.myDevices[self.deviceList.currentRow()]
            self.deviceList.takeItem(self.deviceList.currentRow())
            self.currentDevice = self.myDevices[self.deviceList.currentRow()]
            self.hasEditedCurrentDevice = False
            self.updateFields()

    # When the selected device changes, remember the previous one in case there's an error and we need to go back to it
    def rememberPreviousItem(self, currentItem, previousItem):
        self.previousItem = previousItem
        print "set previous to", self.previousItem.text()

    # Do all the fun stuff when the user clicks on a different device
    # This gives control over whether or not to allow switching to a new device if there are errors with the current one
    def onDeviceClicked(self, item):
        print "Clicked", item.text(), "(row", str(self.deviceList.row(item)) + ")"
        print "Compare", item.text(), "to", self.previousItem.text()
        # Clicked on a different one than was previously selected
        if item != self.previousItem:
            print "different"
            # Ask the user if they want to save any changes that have been made
            if self.hasEditedCurrentDevice:
                saveChanges = QtGui.QMessageBox.question(None, "", "Save changes to current device?",
                                                         QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                         QtGui.QMessageBox.No)
                if saveChanges == QtGui.QMessageBox.Yes:
                    if self.saveHelper():
                        print "save successful"
                        self.previousItem.setText(self.currentDevice.name)
                        self.previousItem = item
                        self.currentDevice = self.myDevices[self.deviceList.currentRow()]
                    else:
                        print "save failed"
                        self.deviceList.setCurrentItem(self.previousItem)
                        # Don't reset all of the fields back to original values if the save failed
                        return
                else:
                    print "not saving new device"
                    # If the device did not already exist, discard it
                    # This is if the user clicks "Add Device" and then selects another device before saving the new one
                    if self.currentDevice.isNew:
                        self.deviceList.takeItem(self.deviceList.row(self.previousItem))
                        self.previousItem = None
                        self.myDevices.pop()
                    self.currentDevice = self.myDevices[self.deviceList.currentRow()]
                    self.hasEditedCurrentDevice = False
                    self.resetValidationExceptions()
            else:
                self.previousItem = item
                self.currentDevice = self.myDevices[self.deviceList.currentRow()]
        else:
            print "same"

        print "current device is", self.currentDevice.name
        self.updateFields()

    # React when self.friendlyNameEdit changes
    def onNameInputChange(self):
        print "name change"
        # Disallow whitespace
        if not self.noWhitespaceRegex.exactMatch(self.friendlyNameEdit.text()) and len(self.friendlyNameEdit.text()) > 0:
            QtGui.QMessageBox.warning(None, "Error", "The name cannot contain whitespace.")
            self.friendlyNameEdit.setText(self.friendlyNameEdit.text()[:-1])
        # Check if modified from original
        self.checkForEdits()

    # React when self.modelNameSelect changes
    def onModelNameChange(self):
        print "model change"
        # Check if modified from original
        self.checkForEdits()

    # React when address type changes
    def onRadioToggle(self, isChecked):
        print "radio toggled"
        # Enable the appropriate GUI components depending on which radio button is selected
        if self.ipRadio.isChecked():
            self.ipWidget.setEnabled(True)
            self.nodeNameWidget.setEnabled(False)
        elif self.nodeRadio.isChecked():
            self.ipWidget.setEnabled(False)
            self.nodeNameWidget.setEnabled(True)
        # Check if modified from original
        self.checkForEdits()

    # React when IP address changes
    def onIPChange(self):
        print "ip changed"
        # Check if modified from original
        self.checkForEdits()

    # React to node name changes
    def onNodeChange(self):
        print "nodename changed"
        # Disallow whitespace
        if not self.noWhitespaceRegex.exactMatch(self.nodeEdit.text()) and len(self.nodeEdit.text()) > 0:
            QtGui.QMessageBox.warning(None, "Error", "The node name cannot contain whitespace.")
            self.nodeEdit.setText(self.nodeEdit.text()[:-1])
        # Check if modified from original
        self.checkForEdits()

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

    def validateFieldValues(self):
        # TODO: Don't save if the name is a duplicate
        # TODO: Decide if fields should be left blank or repopulated with their original values
        # Validate the values entered by the user
        # If there is an error, set flags to keep the save button enabled even if the original value is entered again
        errors = ""
        if len(self.friendlyNameEdit.text()) < 1:
            errors += "You must enter a name."
            self.allowOriginalName = True
        if self.friendlyNameEdit.text() in self.getNames(self.currentDevice):
            errors += "\n" if len(errors) > 0 else ""
            errors += "A device with that name already exists."
            self.allowOriginalName = True
        if len(self.modelNameSelect.currentText()) < 1:
            errors += "\n" if len(errors) > 0 else ""
            errors += "You must select a model."
            self.allowOriginalModel = True
        # TODO: Check for empty text boxes rather than zero IP
        # Not sure if 0.0.0.0 will ever be a valid IP
        if self.ipRadio.isChecked() and self.getIP() == "000.000.000.000":
            errors += "\n" if len(errors) > 0 else ""
            errors += "You must enter an IP address."
            self.allowOriginalAddr = True
        if self.nodeRadio.isChecked() and len(self.nodeEdit.text()) < 1:
            errors += "\n" if len(errors) > 0 else ""
            errors += "You must enter a node name."
            self.allowOriginalAddr = True
        if len(errors) > 0:
            QtGui.QMessageBox.warning(None, "Error", errors)
            return False
        return True

    def resetValidationExceptions(self):
        self.allowOriginalName = False
        self.allowOriginalModel = False
        self.allowOriginalAddr = False

    # Determine if the device has been edited
    # Check if any field values differ from the originals, "OR" the results together
    def checkForEdits(self):
        # Name
        print "checking", self.friendlyNameEdit.text(), "vs", self.currentDevice.name,
        edited = False or self.hasEditedIfNotEqual(self.friendlyNameEdit.text(),
                                                   self.currentDevice.name,
                                                   self.allowOriginalName)
        print edited
        # Model
        print "checking", self.modelNameSelect.currentText(), "vs", self.currentDevice.model,
        edited = edited or self.hasEditedIfNotEqual(self.modelNameSelect.currentText(),
                                                    self.currentDevice.model,
                                                    self.allowOriginalModel)
        print edited
        # IP or Node
        print "checking address",
        if self.ipRadio.isChecked():
            if not self.currentDevice.usesIP:
                print "switched to IP",
                edited = True
            else:
                print "checking", self.getIP(), "vs", self.currentDevice.addr,
                edited = edited or self.hasEditedIfNotEqual(self.getIP(),
                                                            self.currentDevice.addr,
                                                            self.allowOriginalAddr)
        elif self.nodeRadio.isChecked():
            if self.currentDevice.usesIP:
                print "switched to node",
                edited = True
            else:
                print "checking", self.nodeEdit.text(), "vs", self.currentDevice.addr,
                edited = edited or self.hasEditedIfNotEqual(self.nodeEdit.text(),
                                                            self.currentDevice.addr,
                                                            self.allowOriginalAddr)
        print edited

        # Act accordingly
        self.hasEditedCurrentDevice = edited
        print 'EDITED SET TO', edited, 'in checkForEdits'
        self.saveBtn.setEnabled(self.hasEditedCurrentDevice)
        global debugcounter
        print debugcounter, "-------------"
        debugcounter += 1

    def disableSignals(self):
        self.friendlyNameEdit.blockSignals(True)
        self.modelNameSelect.blockSignals(True)
        self.ipRadio.blockSignals(True)
        for box in self.ipEdits:
            box.blockSignals(True)
        self.nodeRadio.blockSignals(True)
        self.nodeEdit.blockSignals(True)

    def enableSignals(self):
        self.friendlyNameEdit.blockSignals(False)
        self.modelNameSelect.blockSignals(False)
        self.ipRadio.blockSignals(False)
        for box in self.ipEdits:
            box.blockSignals(False)
        self.nodeRadio.blockSignals(False)
        self.nodeEdit.blockSignals(False)

    def getNames(self, curr):
        for dev in self.myDevices:
            if dev != curr:
                yield dev.name


def main():
    # Every PyQt4 application must create an application object
    app = QtGui.QApplication(sys.argv)

    window = ConfigWindow()

    # Because 'exec' is a Python keyword, Qt uses 'exec_' instead
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()