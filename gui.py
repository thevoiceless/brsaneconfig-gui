#! /usr/bin/env python

import sys
from PyQt4 import QtGui

def main():
    app = QtGui.QApplication(sys.argv)

    window = QtGui.QWidget()
    window.resize(250, 250)
    window.move(300, 300)
    window.setWindowTitle('brsaneconfig3')
    window.show()

    # Because 'exec' is a Python keyword, 'exec_' was used instead
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()