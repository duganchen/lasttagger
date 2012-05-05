#!/usr/bin/env python

from PyQt4.QtCore import QObject
from PyQt4.QtGui import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                         QLineEdit, QMainWindow, QPushButton, QTableView,
                         QVBoxLayout, QWidget)
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest
from base64 import b64decode
from os import path
import sys


class LastTagger(QMainWindow):

    def __init__(self, parent=None):
        super(LastTagger, self).__init__(parent)

        widget = QWidget()
        layout = QVBoxLayout()

        directoryLayout = QHBoxLayout()
        self.directoryButton = QPushButton('Choose &directory:')
        directoryLayout.addWidget(self.directoryButton)
        self.directoryEdit = QLineEdit()
        self.directoryEdit.setReadOnly(True)
        directoryLayout.addWidget(self.directoryEdit)
        layout.addLayout(directoryLayout)

        albumLayout = QHBoxLayout()
        albumLabel = QLabel('&Album name:')
        albumLayout.addWidget(albumLabel)
        self.albumEdit = QLineEdit()
        albumLabel.setBuddy(self.albumEdit)
        albumLayout.addWidget(self.albumEdit)
        self.albumButton = QPushButton('&Search')
        albumLayout.addWidget(self.albumButton)
        layout.addLayout(albumLayout)

        dataView = QTableView()
        layout.addWidget(dataView)

        self.writeButton = QPushButton('&Write tags')
        self.writeButton.setEnabled(False)
        layout.addWidget(self.writeButton)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def setController(self, controller):
        controller.setView(self)


class LastController(QObject):

    # Yes, this is the same as Quetzalcoatl's.
    __last_fm_key = b64decode('Mjk1YTAxY2ZhNjVmOWU1MjFiZGQyY2MzYzM2ZDdjODk=')

    def __init__(self, parent=None):
        super(LastController, self).__init__(parent)

    def setView(self, view):
        self.setParent(view)
        view.directoryButton.clicked.connect(self.chooseDirectory)

    def chooseDirectory(self):
        directory = QFileDialog.getExistingDirectory(self.parent(),
                                                   'Select Directory',
                                                   path.expanduser('~'),
                                                   QFileDialog.ShowDirsOnly)
        directoryEdit = self.parent().directoryEdit
        directoryEdit.setText(directory)


def main():
    app = QApplication(sys.argv)
    window = LastTagger()
    controller = LastController()
    window.setController(controller)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
