#!/usr/bin/env python

from sip import setapi
setapi("QDate", 2)
setapi("QDateTime", 2)
setapi("QTextStream", 2)
setapi("QTime", 2)
setapi("QVariant", 2)
setapi("QString", 2)
setapi("QUrl", 2)

from PyQt4.QtCore import QObject, Qt, QUrl
from PyQt4.QtGui import (QApplication, QDialog, QDialogButtonBox, QFileDialog,
                         QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                         QPushButton, QTableView, QTreeWidget, QTreeWidgetItem,
                         QVBoxLayout, QWidget)
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest
from base64 import b64decode
from json import loads
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
        self.albumButton.setEnabled(False)
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
        self.__networkManager = QNetworkAccessManager()

    def setView(self, view):
        self.setParent(view)
        view.directoryButton.clicked.connect(self.__chooseDirectory)
        view.albumButton.clicked.connect(self.__searchAlbum)
        view.albumEdit.textEdited.connect(self.__editText)

    def __chooseDirectory(self):
        directory = QFileDialog.getExistingDirectory(self.parent(),
                                                   'Select Directory',
                                                   path.expanduser('~'),
                                                   QFileDialog.ShowDirsOnly)
        directoryEdit = self.parent().directoryEdit
        directoryEdit.setText(directory)

    def __searchAlbum(self):
        album = self.parent().albumEdit.text().strip()
        reply = self.__get_reply({'method': 'album.search',
                                  'album': album})
        reply.finished.connect(self.__loadSearch)

    def __loadSearch(self):
        reply = self.sender()
        json = loads(reply.readAll().data())
        albums = json['results']['albummatches']['album']

        dialog = AlbumDialog(albums, self.parent())
        if dialog.exec_() != QDialog.Accepted:
            return None
        item = dialog.getSelectedItem()
        if item is not None:
            return None
        name, artist = item
        print (name, artist)
        reply.deleteLater()

    def __editText(self, text):
        isEnabled = len(text.strip()) > 0
        self.parent().albumButton.setEnabled(isEnabled)

    def __get_reply(self, params):
        url = QUrl('http://ws.audioscrobbler.com/2.0/')
        url.addQueryItem('api_key', self.__last_fm_key)
        url.addQueryItem('format', 'json')
        for key, value in params.iteritems():
            url.addQueryItem(key, value)
        request = QNetworkRequest(url)
        return self.__networkManager.get(request)


class AlbumDialog(QDialog):

    def __init__(self, albums, parent=None):
        super(AlbumDialog, self).__init__(parent, Qt.Dialog)
        layout = QVBoxLayout()
        self.treeWidget = QTreeWidget()
        self.treeWidget.setHeaderLabels(['Album', 'Artist'])
        layout.addWidget(self.treeWidget)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)
        self.setLayout(layout)

        items = [QTreeWidgetItem([album['name'], album['artist']])
                  for album in albums]
        self.treeWidget.addTopLevelItems(items)

    def getSelectedItem(self):
        items = self.treeWidget.selectedItems()
        if len(items) == 0:
            return None
        item = items[0]
        return (item.data(0, Qt.DisplayRole), item.data(1, Qt.DisplayRole))


def main():
    app = QApplication(sys.argv)
    window = LastTagger()
    controller = LastController()
    window.setController(controller)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
