Last Tagger
===========

The Last Tagger is a Last.fm-backed album tagger.

Use it to prepare an already-tagged collection for use with
Last.fm-enabled software. It will write the relevant tag subset`&mdash;`album,
artist, album artist, track number and their corresponding mbid tags`&mdash;`to the values that last.fm expects.

Dependencies
------------

* [PyQt4](http://www.riverbankcomputing.com/software/pyqt)
* [Mutagen](http://code.google.com/p/mutagen)
* [lxml](http://lxml.de)

If you can install these dependencies, then you can run Last Tagger.

Last Tagger will support the same audio file formats that your Mutagen
installation supports. On most installations, that's *every* format.

Instructions
------------

You can tag one directory at a time.

1. Select a music directory
2. Enter the name of the album
3. Click "search"
4. Choose the album from the dialog box
5. Choose "Write Tags"
