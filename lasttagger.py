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
                         QHBoxLayout, QLabel, QLineEdit, QListWidget,
                         QMainWindow, QMessageBox, QPushButton, QSplitter,
                         QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest
from base64 import b64decode
from json import loads
from os import listdir
from os.path import expanduser, realpath
import sys


class LastTagger(QMainWindow):

    def __init__(self, parent=None):
        super(LastTagger, self).__init__(parent)

        widget = QWidget()
        layout = QVBoxLayout()

        splitter = QSplitter()
        fileLayout = QVBoxLayout()

        directoryLayout = QHBoxLayout()
        self.directoryButton = QPushButton('Choose &directory:')
        directoryLayout.addWidget(self.directoryButton)
        self.directoryEdit = QLineEdit()
        self.directoryEdit.setReadOnly(True)
        directoryLayout.addWidget(self.directoryEdit)
        fileLayout.addLayout(directoryLayout)
        self.fileList = QListWidget()
        fileLayout.addWidget(self.fileList)
        directoryWidget = QWidget()
        directoryWidget.setLayout(fileLayout)
        splitter.addWidget(directoryWidget)

        albumLayout = QHBoxLayout()
        albumLabel = QLabel('&Album name:')
        albumLayout.addWidget(albumLabel)
        self.albumEdit = QLineEdit()
        albumLabel.setBuddy(self.albumEdit)
        albumLayout.addWidget(self.albumEdit)
        self.albumButton = QPushButton('&Search')
        self.albumButton.setEnabled(False)
        albumLayout.addWidget(self.albumButton)
        tagLayout = QVBoxLayout()
        tagLayout.addLayout(albumLayout)
        self.trackList = QListWidget()
        tagLayout.addWidget(self.trackList)
        albumWidget = QWidget()
        albumWidget.setLayout(tagLayout)
        splitter.addWidget(albumWidget)

        layout.addWidget(splitter)

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
                                                   realpath(expanduser('~')),
                                                   QFileDialog.ShowDirsOnly)
        directory = realpath(directory)
        directoryEdit = self.parent().directoryEdit
        directoryEdit.setText(directory)

        for i in reversed(range(self.parent().fileList.count())):
            self.parent().fileList.takeItem(i)

        for filename in sorted(listdir(directory)):
            self.parent().fileList.addItem(filename)

    def __searchAlbum(self):
        album = self.parent().albumEdit.text().strip()
        reply = self.__get_reply({'method': 'album.search',
                                  'album': album})
        reply.finished.connect(self.__loadSearch)

    def __loadSearch(self):
        reply = self.sender()
        json = loads(reply.readAll().data())
        reply.deleteLater()

        matches = json['results']['albummatches']
        if type(matches) != dict:
            QMessageBox.information(self.parent(),
                                    'No albums found',
                                    'No albums found')
            return
        albums = matches['album']

        dialog = AlbumDialog(albums, self.parent())
        if dialog.exec_() != QDialog.Accepted:
            return None
        item = dialog.getSelectedItem()
        if item is None:
            return None
        name, artist = item

        reply = self.__get_reply({'method': 'album.getinfo',
                                  'album': name,
                                  'artist': artist})
        reply.finished.connect(self.__load_tracks)

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

    def __load_tracks(self):
        reply = self.sender()
        json = loads(reply.readAll().data())
        reply.deleteLater()
        tracks = [x['name'] for x in json['album']['tracks']['track']]
        for i in reversed(range(self.parent().trackList.count())):
            self.parent().trackList.takeItem(i)
        for track in tracks:
            self.parent().trackList.addItem(track)


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
