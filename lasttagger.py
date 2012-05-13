#!/usr/bin/env python

from sip import setapi
setapi("QDate", 2)
setapi("QDateTime", 2)
setapi("QTextStream", 2)
setapi("QTime", 2)
setapi("QVariant", 2)
setapi("QString", 2)
setapi("QUrl", 2)

from PyQt4.QtCore import (QAbstractListModel, QModelIndex, QObject, Qt, QUrl,
                          pyqtSignal)
from PyQt4.QtGui import (QApplication, QDialog, QDialogButtonBox, QFileDialog,
                         QHBoxLayout, QLabel, QLineEdit, QListView,
                         QMainWindow, QMessageBox, QPushButton, QSplitter,
                         QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from PyQt4.QtNetwork import QNetworkAccessManager, QNetworkRequest
from base64 import b64decode
from json import loads
from mutagen import File
from os import listdir
from os.path import basename, exists, expanduser, isfile, join, realpath
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
        fileView = QListView()
        self.fileModel = FileModel(fileView)
        fileView.setModel(self.fileModel)
        fileLayout.addWidget(fileView)
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
        trackView = QListView()
        self.trackModel = TrackModel(trackView)
        trackView.setModel(self.trackModel)
        tagLayout.addWidget(trackView)
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

    writable = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(LastController, self).__init__(parent)
        self.__networkManager = QNetworkAccessManager()

    def setView(self, view):
        self.setParent(view)
        view.directoryButton.clicked.connect(self.__chooseDirectory)
        view.albumButton.clicked.connect(self.__searchAlbum)
        view.albumEdit.textEdited.connect(self.__editText)
        self.writable.connect(view.writeButton.setEnabled)
        view.writeButton.clicked.connect(self.__writeTracks)

    def __chooseDirectory(self):
        user = realpath(expanduser('~'))
        music = realpath(join(user, 'Music'))
        start = music if exists(music) else user
        directory = QFileDialog.getExistingDirectory(self.parent(),
                                                   'Select Directory',
                                                   start,
                                                   QFileDialog.ShowDirsOnly)
        directory = realpath(directory)
        directoryEdit = self.parent().directoryEdit
        directoryEdit.setText(directory)

        paths = (realpath(join(directory, filename))
                 for filename in sorted(listdir(directory)))
        files = (File(path) for path in paths if isfile(path))
        songs = [song for song in files if song is not None]
        self.parent().fileModel.empty()
        self.parent().fileModel.addItems(songs)
        self.__checkWritable()

    def __searchAlbum(self):
        album = self.parent().albumEdit.text().strip()
        reply = self.__getReply({'method': 'album.search',
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

        reply = self.__getReply({'method': 'album.getinfo',
                                  'album': name,
                                  'artist': artist})
        reply.finished.connect(self.__loadTracks)

    def __editText(self, text):
        isEnabled = len(text.strip()) > 0
        self.parent().albumButton.setEnabled(isEnabled)

    def __getReply(self, params):
        url = QUrl('http://ws.audioscrobbler.com/2.0/')
        url.addQueryItem('api_key', self.__last_fm_key)
        url.addQueryItem('format', 'json')
        for key, value in params.iteritems():
            url.addQueryItem(key, value)
        request = QNetworkRequest(url)
        return self.__networkManager.get(request)

    def __loadTracks(self):
        reply = self.sender()
        json = loads(reply.readAll().data())
        reply.deleteLater()
        self.parent().trackModel.empty()
        if type(json['album']['tracks']) != dict:
            QMessageBox.information(self.parent(),
                                    'No tracks found',
                                    'No tracks found')
            return
        self.parent().trackModel.addItems(json['album']['tracks']['track'])
        self.__checkWritable()

    def __checkWritable(self):
        hasFiles = self.parent().fileModel.rowCount() > 0
        hasTracks = self.parent().trackModel.rowCount() > 0
        self.writable.emit(hasFiles and hasTracks)

    def __writeTracks(self):
        print 'Writing tracks'


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


class ListModel(QAbstractListModel):

    def __init__(self, parent=None):
        super(ListModel, self).__init__(parent)
        self._items = []

    def addItems(self, items):
        top = len(self._items)
        self.beginInsertRows(QModelIndex(), top, top + len(items))
        self._items.extend(items)
        self.endInsertRows()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if index.row() > len(self._items):
            return None

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self.getData(index.row()).decode('utf-8')

        return None

    def empty(self):
        self.beginRemoveRows(QModelIndex(), 0, len(self._items) - 1)
        del self._items[:]
        self.endRemoveRows()

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)


class FileModel(ListModel):

    def __init__(self, parent=None):
        super(FileModel, self).__init__(parent)

    def getData(self, row):
        return basename(self._items[row].filename)


class TrackModel(ListModel):
    def __init__(self, parent=None):
        super(TrackModel, self).__init__(parent)

    def getData(self, row):
        return self._items[row]['name']


def main():
    app = QApplication(sys.argv)
    window = LastTagger()
    controller = LastController()
    window.setController(controller)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
