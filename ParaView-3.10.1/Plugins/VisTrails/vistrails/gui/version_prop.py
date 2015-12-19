
############################################################################
##
## This file is part of the Vistrails ParaView Plugin.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following to ensure GNU General Public
## Licensing requirements will be met:
## http://www.opensource.org/licenses/gpl-2.0.php
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
############################################################################

############################################################################
##
## Copyright (C) 2006, 2007, 2008 University of Utah. All rights reserved.
##
############################################################################
""" This file describe a widget for keeping version notes,info and tag
name

QVersionProp
QVersionNotes
QVersionPropOverlay
QExpandButton
QNotesDialog
"""
import sys
import os
import tempfile
import time
import shutil
import zipfile
from PyQt4 import QtCore, QtGui
from PyQt4.phonon import Phonon
from gui.utils import getBuilderWindow
from core.vistrail.action import Action
from core.query.version import SearchCompiler, SearchParseError, TrueSearch
from gui.theme import CurrentTheme
from gui.common_widgets import QToolWindowInterface
from gui.common_widgets import QSearchBox
from gui.video_player import VideoMainWindow
from core.utils import all

################################################################################

class QVersionProp(QtGui.QWidget, QToolWindowInterface):
    """
    QVersionProp is a widget holding property of a version including
    tagname and notes
    
    """    
    def __init__(self, parent=None):
        """ QVersionProp(parent: QWidget) -> QVersionProp
        Initialize the main layout
        
        """
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('Properties')

        vLayout = QtGui.QVBoxLayout()
        vLayout.setMargin(0)
        vLayout.setSpacing(5)
        self.setLayout(vLayout)

        self.searchBox = QSearchBox(self)
        vLayout.addWidget(self.searchBox)
        
        gLayout = QtGui.QGridLayout()
        gLayout.setMargin(0)
        gLayout.setSpacing(5)
        gLayout.setColumnMinimumWidth(1,5)
        gLayout.setRowMinimumHeight(0,24)
        gLayout.setRowMinimumHeight(1,24)
        gLayout.setRowMinimumHeight(2,24)
        gLayout.setRowMinimumHeight(3,24)        
        vLayout.addLayout(gLayout)
        
        tagLabel = QtGui.QLabel('Tag:', self)
        gLayout.addWidget(tagLabel, 0, 0, 1, 1)

        editLayout = QtGui.QHBoxLayout()
        editLayout.setMargin(0)
        editLayout.setSpacing(2)
        self.tagEdit = QtGui.QLineEdit()
        tagLabel.setBuddy(self.tagEdit)
        editLayout.addWidget(self.tagEdit)
        self.tagEdit.setEnabled(False)

        self.tagReset = QtGui.QToolButton(self)
        self.tagReset.setIcon(QtGui.QIcon(
                self.style().standardPixmap(QtGui.QStyle.SP_DialogCloseButton)))
        self.tagReset.setIconSize(QtCore.QSize(12,12))
        self.tagReset.setAutoRaise(True)
        self.tagReset.setEnabled(False)
        editLayout.addWidget(self.tagReset)

        gLayout.addLayout(editLayout, 0, 2, 1, 1)

        userLabel = QtGui.QLabel('User:', self)
        gLayout.addWidget(userLabel, 1, 0, 1, 1)
        
        self.userEdit = QtGui.QLabel('', self)
        gLayout.addWidget(self.userEdit, 1, 2, 1, 1)

        dateLabel = QtGui.QLabel('Date:', self)
        gLayout.addWidget(dateLabel, 2, 0, 1, 1)

        self.dateEdit = QtGui.QLabel('', self)
        gLayout.addWidget(self.dateEdit, 2, 2, 1, 1)

        self.notesLabel = QtGui.QLabel('Notes:')
        gLayout.addWidget(self.notesLabel, 3, 0, 1, 1)

        self.versionNotes = QVersionNotes()
        vLayout.addWidget(self.versionNotes)
        self.versionNotes.setEnabled(False)

        self.versionEmbed = QVersionEmbed()
        vLayout.addWidget(self.versionEmbed)
        self.versionEmbed.setVisible(False)
        
        self.connect(self.tagEdit, QtCore.SIGNAL('editingFinished()'),
                     self.tagFinished)
        self.connect(self.tagEdit, QtCore.SIGNAL('textChanged(QString)'),
                     self.tagChanged)
        self.connect(self.tagReset, QtCore.SIGNAL('clicked()'),
                     self.tagCleared)
        self.connect(self.searchBox, QtCore.SIGNAL('resetSearch()'),
                     self.resetSearch)
        self.connect(self.searchBox, QtCore.SIGNAL('executeSearch(QString)'),
                     self.executeSearch)
        self.connect(self.searchBox, QtCore.SIGNAL('refineMode(bool)'),
                     self.refineMode)

        self.controller = None
        self.versionNumber = -1
        self.refineMode(False)

    def updateController(self, controller):
        """ updateController(controller: VistrailController) -> None
        Assign the controller to the property page
        
        """
        self.controller = controller
        self.versionNotes.controller = controller
        self.versionEmbed.controller = controller

    def updateVersion(self, versionNumber):
        """ updateVersion(versionNumber: int) -> None
        Update the property page of the version
        
        """
        self.versionNumber = versionNumber
        self.versionNotes.updateVersion(versionNumber)
        self.versionEmbed.updateVersion(versionNumber)
        
        if self.controller:
            if self.controller.vistrail.actionMap.has_key(versionNumber):
                action = self.controller.vistrail.actionMap[versionNumber]
                name = self.controller.vistrail.getVersionName(versionNumber)
                self.tagEdit.setText(name)
                self.userEdit.setText(action.user)
                self.dateEdit.setText(action.date)
                self.tagEdit.setEnabled(True)
                self.versionEmbed.setVisible(self.versionEmbed.check_version() and
                                            versionNumber > 0)
                return
            else:
                self.tagEdit.setEnabled(False)
                self.tagReset.setEnabled(False)
        self.tagEdit.setText('')
        self.userEdit.setText('')
        self.dateEdit.setText('')
        

    def tagFinished(self):
        """ tagFinished() -> None
        Update the new tag to vistrail
        
        """
        if self.controller:
            self.controller.update_current_tag(str(self.tagEdit.text()))

    def tagChanged(self, text):
        """ tagChanged(text: QString) -> None
        Update the button state if there is text

        """
        self.tagReset.setEnabled(text != '')

    def tagCleared(self):
        """ tagCleared() -> None
        Remove the tag
        
        """ 
        self.tagEdit.setText('')
        self.tagFinished()
        
    def resetSearch(self, emit_signal=True):
        """
        resetSearch() -> None

        """
        if self.controller and emit_signal:
            self.controller.set_search(None)
            self.emit(QtCore.SIGNAL('textQueryChange(bool)'), False)
        else:
            self.searchBox.clearSearch()
    
    def executeSearch(self, text):
        """
        executeSearch(text: QString) -> None

        """
        s = str(text)
        if self.controller:
            try:
                search = SearchCompiler(s).searchStmt
            except SearchParseError, e:
                QtGui.QMessageBox.warning(self,
                                          QtCore.QString("Search Parse Error"),
                                          QtCore.QString(str(e)),
                                          QtGui.QMessageBox.Ok,
                                          QtGui.QMessageBox.NoButton,
                                          QtGui.QMessageBox.NoButton)
                search = None
            self.controller.set_search(search, s)
            self.emit(QtCore.SIGNAL('textQueryChange(bool)'), s!='')

    def refineMode(self, on):
        """
        refineMode(on: bool) -> None
        
        """
        if self.controller:
            self.controller.set_refine(on)

class QVersionNotes(QtGui.QTextEdit):
    """
    QVersionNotes is text widget that update/change a version notes
    
    """    
    def __init__(self, parent=None):
        """ QVersionNotes(parent: QWidget) -> QVersionNotes
        Initialize control variables
        
        """
        QtGui.QTextEdit.__init__(self, parent)
        self.controller = None
        self.versionNumber = -1
        self.update_on_focus_out = True
        # Reset text to black, for some reason it is grey by default on the mac
        self.palette().setBrush(QtGui.QPalette.Text,
                                QtGui.QBrush(QtGui.QColor(0,0,0,255)))
        self.setFont(CurrentTheme.VERSION_PROPERTIES_FONT)

    def updateVersion(self, versionNumber):
        """ updateVersion(versionNumber: int) -> None
        Update the text to be the notes of the vistrail versionNumber
        
        """
        self.versionNumber = versionNumber
        if self.controller:
            if self.controller.vistrail.actionMap.has_key(versionNumber):
                action = self.controller.vistrail.actionMap[versionNumber]
                if action.notes:
                    self.setHtml(action.notes)
                    # work around a strange bug where an empty new paragraph gets added every time
                    self.trim_first_paragraph()
                else:
                    self.setHtml('')
                self.setEnabled(True)
                return
            else:
                self.setEnabled(False)
        self.setPlainText('')

    def commit_changes(self):
        if self.controller and self.document().isModified():
            self.controller.update_notes(str(self.toHtml()))

    def reset_changes(self):
        """ reset_changes() -> None

        """
        self.updateVersion(self.versionNumber)

    def focusOutEvent(self, event):
        """ focusOutEvent(event: QFocusEvent) -> None
        Update the version notes if the text has been modified
        
        """
        if self.update_on_focus_out:
            self.commit_changes()
        QtGui.QTextEdit.focusOutEvent(self,event)

    def trim_first_paragraph(self):
        doc = self.document()
        count = doc.blockCount()
        cursor = QtGui.QTextCursor(doc)
        cursor.select(QtGui.QTextCursor.LineUnderCursor)
        sel = cursor.selection().toPlainText()
        if all(sel, lambda c: c == ' '):
            cursor.removeSelectedText()
            cursor = QtGui.QTextCursor(doc)
            cursor.deleteChar()



videoControl = None


################################################################################
class QVersionPropOverlay(QtGui.QFrame):
    """
    QVersionPropOverlay is a transparent widget that sits on top of the version
    view.  It displays properties of a version: tag, user, date, and notes.

    """
    propagatingEvent = set([
        QtCore.QEvent.MouseButtonDblClick,
        QtCore.QEvent.MouseButtonPress,
        QtCore.QEvent.MouseButtonRelease,
        QtCore.QEvent.MouseMove,
        QtCore.QEvent.Wheel,
        ])
    def __init__(self, parent=None, mouseWidget=None):
        """ QVersionPropOverlay(parent: QWidget) -> QVersionPropOverlay
        Setup layout

        """
        QtGui.QFrame.__init__(self, parent)
        self.propagatingWidget = mouseWidget
        self.palette = QtGui.QPalette()
        self.palette.setColor(QtGui.QPalette.Base, QtGui.QColor(0,0,0,0))
        self.setPalette(self.palette)
        self.setAutoFillBackground(True)
        self.setFrameStyle(QtGui.QFrame.NoFrame)
        self.setFrameShadow(QtGui.QFrame.Plain)
        self.layout = QtGui.QGridLayout()
        self.layout.setVerticalSpacing(1)
        

        self.tag_label = QtGui.QLabel()
        self.tag_label.palette().setBrush(QtGui.QPalette.Text,
                                          CurrentTheme.VERSION_PROPERTIES_PEN)
        self.tag_label.setFont(CurrentTheme.VERSION_PROPERTIES_FONT)
        self.tag_label.setText(QtCore.QString("Tag:"))

        self.tag = QtGui.QLabel()
        self.tag.setFont(CurrentTheme.VERSION_PROPERTIES_FONT)

        self.tag_layout = QtGui.QHBoxLayout()
        self.tag_layout.addWidget(self.tag)
        self.tag_layout.addStretch()

        self.description_label = QtGui.QLabel()
        self.description_label.palette().setBrush(QtGui.QPalette.Text,
                                                  CurrentTheme.VERSION_PROPERTIES_PEN)
        self.description_label.setFont(CurrentTheme.VERSION_PROPERTIES_FONT)
        self.description_label.setText(QtCore.QString("Action:"))

        self.description = QtGui.QLabel()
        self.description.setFont(CurrentTheme.VERSION_PROPERTIES_FONT)

        self.description_layout = QtGui.QHBoxLayout()
        self.description_layout.addWidget(self.description)
        self.description_layout.addStretch()

        self.user_label = QtGui.QLabel()
        self.user_label.palette().setBrush(QtGui.QPalette.Text,
                                           CurrentTheme.VERSION_PROPERTIES_PEN)
        self.user_label.setFont(CurrentTheme.VERSION_PROPERTIES_FONT)
        self.user_label.setText(QtCore.QString("User:"))

        self.user = QtGui.QLabel()
        self.user.setFont(CurrentTheme.VERSION_PROPERTIES_FONT)

        self.user_layout = QtGui.QHBoxLayout()
        self.user_layout.addWidget(self.user)
        self.user_layout.addStretch()

        self.date_label = QtGui.QLabel()
        self.date_label.palette().setBrush(QtGui.QPalette.Text,
                                           CurrentTheme.VERSION_PROPERTIES_PEN)
        self.date_label.setFont(CurrentTheme.VERSION_PROPERTIES_FONT)
        self.date_label.setText(QtCore.QString("Date:"))
        
        self.date = QtGui.QLabel()
        self.date.setFont(CurrentTheme.VERSION_PROPERTIES_FONT)

        self.date_layout = QtGui.QHBoxLayout()
        self.date_layout.addWidget(self.date)
        self.date_layout.addStretch()

        #NOTES

        self.notes_label = QtGui.QLabel()
        self.notes_label.palette().setBrush(QtGui.QPalette.Text,
                                           CurrentTheme.VERSION_PROPERTIES_PEN)
        self.notes_label.setFont(CurrentTheme.VERSION_PROPERTIES_FONT)
        self.notes_label.setText(QtCore.QString("Notes:"))

        self.notes = QtGui.QLabel()
        self.notes.setTextFormat(QtCore.Qt.RichText)
        self.notes.setFont(CurrentTheme.VERSION_PROPERTIES_FONT)
        
        self.notes_button = QExpandButton()
        self.notes_button.hide()

        self.notes_layout = QtGui.QHBoxLayout()
        self.notes_layout.addWidget(self.notes)
        self.notes_layout.addSpacing(5)
        self.notes_layout.addWidget(self.notes_button)
        self.notes_layout.addStretch()

        
        #Added video here
        self.videofname = None
        self.videoDeleted = False
        self.video_label = QtGui.QLabel()
        self.video_label.palette().setBrush(QtGui.QPalette.Text,
                                                  CurrentTheme.VERSION_PROPERTIES_PEN)
        self.video_label.setFont(CurrentTheme.VERSION_PROPERTIES_FONT)
        self.video_label.setText(QtCore.QString("Video:"))

        self.video = QtGui.QLabel()
        self.video.setTextFormat(QtCore.Qt.RichText)
        self.video.setFont(CurrentTheme.VERSION_PROPERTIES_FONT)

        self.open_video_button = QOpenVideo()
        self.open_video_button.hide()

        self.delete_video_button = QDeleteVideoButton()
        self.delete_video_button.hide()

        self.video_layout = QtGui.QHBoxLayout()
        self.video_layout.addWidget(self.video)
        self.video_layout.addSpacing(5)
        self.video_layout.addWidget(self.open_video_button)
        self.video_layout.addWidget(self.delete_video_button)
        self.video_layout.addStretch()
        
        #Added audio here
        self.audioMedia = None
        self.audio_label = QtGui.QLabel()
        self.audio_label.palette().setBrush(QtGui.QPalette.Text,
                                                 CurrentTheme.VERSION_PROPERTIES_PEN)
        self.audio_label.setFont(CurrentTheme.VERSION_PROPERTIES_FONT)
        self.audio_label.setText(QtCore.QString("Audio:"))

        self.audio = QtGui.QLabel()
        self.audio.setTextFormat(QtCore.Qt.RichText)
        self.audio.setFont(CurrentTheme.VERSION_PROPERTIES_FONT)

        self.play_audio_button = QPlayButton()
        self.play_audio_button.hide()

        self.pause_audio_button = QPauseButton()
        self.pause_audio_button.hide()

        self.stop_audio_button = QStopButton()
        self.stop_audio_button.hide()

        self.open_audio_button = QOpenMultimediaButton()
        self.open_audio_button.hide()

        self.delete_audio_button = QDeleteButton()
        self.delete_audio_button.hide()

        self.audio_layout = QtGui.QHBoxLayout()
        self.audio_layout.addWidget(self.audio)
        self.audio_layout.addSpacing(5)
        self.audio_layout.addWidget(self.open_audio_button)
        self.audio_layout.addWidget(self.play_audio_button)
        self.audio_layout.addWidget(self.pause_audio_button)
        self.audio_layout.addWidget(self.stop_audio_button)
        self.audio_layout.addWidget(self.delete_audio_button)
        self.audio_layout.addStretch()

        #Details

        self.details_label = QtGui.QLabel()
        self.details_label.palette().setBrush(QtGui.QPalette.Text,
                                              CurrentTheme.VERSION_PROPERTIES_PEN)
        self.details_label.setFont(CurrentTheme.VERSION_PROPERTIES_FONT)
        self.details_label.setText(QtCore.QString("Details:"))

        self.details = QtGui.QLabel()
        self.details.setTextFormat(QtCore.Qt.PlainText)
        self.details.setFont(CurrentTheme.VERSION_PROPERTIES_FONT)

        self.details_layout = QtGui.QHBoxLayout()
        self.details_layout.addWidget(self.details)
        self.details_layout.addStretch()

        self.layout.addWidget(self.tag_label, 0, 0)
        self.layout.addLayout(self.tag_layout, 0, 1)
        self.layout.addWidget(self.description_label, 1, 0)
        self.layout.addLayout(self.description_layout, 1, 1)
        self.layout.addWidget(self.user_label, 2, 0)
        self.layout.addLayout(self.user_layout, 2, 1)
        self.layout.addWidget(self.date_label, 3, 0)
        self.layout.addLayout(self.date_layout, 3, 1)

        self.layout.addWidget(self.notes_label, 4, 0)
        self.layout.addLayout(self.notes_layout, 4, 1)


        self.layout.addWidget(self.audio_label, 5, 0)
        self.layout.addLayout(self.audio_layout, 5,1)


        self.layout.addWidget(self.video_label, 6, 0)
        self.layout.addLayout(self.video_layout, 6,1)

       
        self.layout.addWidget(self.details_label, 8, 0)
        self.layout.addLayout(self.details_layout, 8, 1)

        self.layout.setColumnMinimumWidth(0,35)
        self.layout.setColumnMinimumWidth(1,200)
        self.layout.setContentsMargins(2,2,2,2)
        self.layout.setColumnStretch(1,1)
        self.setLayout(self.layout)
        self.updateGeometry()
        self.controller = None
        
        self.notes_dialog = QNotesDialog(self)
        self.notes_dialog.hide()
       


        QtCore.QObject.connect(self.notes_button,
                               QtCore.SIGNAL("pressed()"),
                               self.openNotes)

        QtCore.QObject.connect(self.open_audio_button,
                               QtCore.SIGNAL("pressed()"),
                               self.openMultimedia)

        QtCore.QObject.connect(self.play_audio_button,
                               QtCore.SIGNAL("pressed()"),
                               self.playAudio)

        QtCore.QObject.connect(self.pause_audio_button,
                               QtCore.SIGNAL("pressed()"),
                               self.pauseAudio)

        QtCore.QObject.connect(self.stop_audio_button,
                               QtCore.SIGNAL("pressed()"),
                               self.stopAudio)

        QtCore.QObject.connect(self.delete_audio_button,
                              QtCore.SIGNAL("pressed()"),
                              self.deleteAudio)

        QtCore.QObject.connect(self.open_video_button,
                               QtCore.SIGNAL("pressed()"),
                               self.openVideo)

        QtCore.QObject.connect(self.delete_video_button,
                               QtCore.SIGNAL("pressed()"),
                               self.deleteVideo)

        
    def updateGeometry(self):
        """ updateGeometry() -> None
        Keep in upper left of screen

        """
        parentGeometry = self.parent().geometry()
        self.pos_x = 4
        self.pos_y = 4
        self.move(self.pos_x, self.pos_y)

    def updateController(self, controller):
        """ updateController(controller: VistrailController) -> None
        Assign the controller to the properties
        
        """
        self.controller = controller
        self.notes_dialog.updateController(controller)

    def updateVersion(self, versionNumber):
        """ updateVersion(versionNumber: int) -> None
        Update the text items
        
        """
        self.notes_dialog.updateVersion(versionNumber)
        if self.controller:
            if self.controller.vistrail.actionMap.has_key(versionNumber):
                action = self.controller.vistrail.actionMap[versionNumber]
                name = self.controller.vistrail.getVersionName(versionNumber)
                description = self.controller.vistrail.get_description(versionNumber)
                self.tag.setText(self.truncate(QtCore.QString(name)))
                self.description.setText(self.truncate(QtCore.QString(description)))
                self.user.setText(self.truncate(QtCore.QString(action.user)))
                self.date.setText(self.truncate(QtCore.QString(action.date)))
                if action.notes:
                    s = self.convertHtmlToText(QtCore.QString(action.notes))
                    self.notes.setText(self.truncate(s))
                else:
                    self.notes.setText('')
                self.notes_button.show()
                self.open_audio_button.show()
                self.open_video_button.show()
                self.audio_filename = action.audio
                self.video_filename = action.video
                if self.controller.videoMediaObject != None:
                    self.controller.videoMediaObject.filename = self.video_filename
                else:
                    self.controller.videoMediaObject.stopVideo()
                    self.controller.videoMediaObject.exitVideo()
                
            else:
                self.tag.setText('')
                self.description.setText('')
                self.user.setText('')
                self.date.setText('')
                self.notes.setText('')
                self.notes_button.hide()
                self.open_audio_button.hide()
                self.open_video_button.show()
                self.audio_filename = None
                self.video_filename = None

    def convertHtmlToText(self, str):
        """ convertHtmlToText(str: QString) -> QString
        Remove HTML tags and newlines
        
        """
        # Some text we want to ignore lives outside brackets in the header
        str.replace(QtCore.QRegExp("<head>.*</head>"), "")
        # Remove all other tags
        str.replace(QtCore.QRegExp("<[^>]*>"), "")
        # Remove newlines
        str.replace(QtCore.QRegExp("\n"), " ")
        return str

    def truncate(self, str):
        """ truncate(str: QString) -> QString
        Shorten string to fit in smaller space
        
        """
        if (str.size() > 24):
            str.truncate(22)
            str.append("...")
        str.replace(QtCore.QRegExp("\n"), "...\n")
        return str


    def extract_file(self, filename, extractDir, zipFilename, mediaType):
        if filename == None or extractDir == None or zipFilename == None:
            return 1
        
        afile = os.path.join(extractDir, mediaType, filename)
        if os.path.exists(afile):
            return 0
        try:
            zf = zipfile.ZipFile(zipFilename, 'r')
        except:
            raise Exception('Error opening file!\nThe file may be invalid or you\nmay have insufficient permissions.')
    
        getBuilderWindow().startProgress('Opening...')
        
        sourceZip = zipfile.ZipFile(zipFilename)
        for name in sourceZip.namelist():
            if name.find(filename) != -1:
                getBuilderWindow().updateProgress(0.5)
                sourceZip.extract(name, extractDir)
                break
            
        getBuilderWindow().endProgress()
        return 0


    def openMultimedia(self):
        if self.controller.audio_dir:
            pass
        else:
            self.controller.audio_dir = tempfile.mkdtemp(prefix="VTAudio")

        tmp_dir = os.path.join(self.controller.audio_dir, "audio")

        if os.path.isdir(tmp_dir) == True:
            pass
        else:
            os.mkdir(os.path.join(self.controller.audio_dir, "audio"))
        
        
        self.audioMedia = Phonon.MediaObject()
        self.audioOutput = Phonon.AudioOutput(Phonon.MusicCategory)
        Phonon.createPath(self.audioMedia, self.audioOutput)
        self.paused = False
        
        self.filename = QtGui.QFileDialog.getOpenFileName(self, 'Open File', 
                                                         '/', "Music (*.mp3 *.wav *.ogg *.mpc *.flac *.au *.raw *.dct *.aac *.m4a *.wma *.amr *.awb)")

        if self.filename != "":
            bname = os.path.basename(str(self.filename))
            fbasename, fextension = os.path.splitext(bname)
            fd, temp_fname = tempfile.mkstemp(suffix=fextension, prefix="VTAudio", dir=tmp_dir) 
            os.close(fd)
            self.file = open(self.filename, 'r')
            shutil.copyfile(self.filename, temp_fname)
            self.audio_filename = temp_fname
            self.fname = os.path.basename(temp_fname)
            self.controller.setAudioMediaObject(self.audioMedia)
            self.controller.update_audio(self.fname)   
        
    def deleteAudio(self):
        if self.audio_filename:
            fname = os.path.join(self.controller.audio_dir, "audio", self.audio_filename)
            print "Removed , ", fname
            if os.path.isfile(fname):
                self.audioMedia.stop()
                os.remove(fname)
                self.controller.update_audio("")
                self.play_audio_button.hide()
                self.pause_audio_button.hide()
                self.stop_audio_button.hide()
                self.delete_audio_button.hide()
    
            
    def loadPhonon(self):
        self.audioMedia = Phonon.MediaObject()
        self.audioOutput = Phonon.AudioOutput(Phonon.MusicCategory)
        Phonon.createPath(self.audioMedia, self.audioOutput)
        self.controller.setAudioMediaObject(self.audioMedia)

    def loadAudio(self):
        if self.audioMedia != None:
            afile = os.path.join(self.controller.audio_dir, "audio", self.audio_filename)
            self.audioMedia.setCurrentSource(Phonon.MediaSource(QtCore.QUrl.fromLocalFile(afile)))
        
   
    def playAudio(self):
        self.extract_file(self.audio_filename, self.controller.audio_dir, self.controller.file_name, "audio")
        
        if self.audioMedia == None:
            self.loadPhonon()
            self.loadAudio()
        self.filename = self.audio_filename
        if self.audioMedia == None:
            self.loadPhonon()
        try:
            if self.filename:
                self.audioMedia.play()
        except Exception:
            raise Exception("Unable to play file format")
        
    def stopAudio(self):
        self.audioMedia.stop()
      
    def pauseAudio(self):
        self.audioMedia.pause()

    def openNotes(self):
        """ openNotes() -> None

        Show notes dialog
        """
        self.notes_dialog.show()
        self.notes_dialog.activateWindow()

    def event(self, e):
        """ Propagate all mouse events to the right widget """
        if e.type() in self.propagatingEvent:
            if self.propagatingWidget!=None:
                QtCore.QCoreApplication.sendEvent(self.propagatingWidget, e)
                return False
        return QtGui.QFrame.event(self, e)

    
    #Video 
    def openVideo(self):
        global videoControl
        self.extract_file(self.video_filename, self.controller.video_dir, self.controller.file_name, "video")
        #If video was deleted by user, and the user is attempting to add another video 
        if self.videoDeleted == True and self.video_filename == None:
            if videoControl == None:
                videoControl = VideoMainWindow()
            videoControl.setVideoDir(self.controller.video_dir)
            vstatus, vdir, vfname = videoControl.open()
            if vstatus == True:
                self.video_filename = os.path.join(vdir, "video", vfname)
                self.controller.update_video(vfname)
                videoControl.setVideoFilename(vfname)
                videoControl.show()
                self.delete_video_button.show()
                self.videoDeleted = False

        #If user is attempting to add a video annotation for the first time
        else:
            #If videoControl object has not been initialized
            if videoControl == None:
                videoControl = VideoMainWindow()
                if self.controller.video_dir == None:
                    pass
                if self.video_filename == None:
                    pass
                else:
                    fname = os.path.join(self.controller.video_dir, "video", self.video_filename)
                    self.controller.update_video(os.path.basename(fname))
                    
                    
            #If videoControl object has been initialized and video filename is not set yet
            if self.video_filename == None:
                if self.controller.video_dir != None:
                    videoControl.setVideoDir(self.controller.video_dir)
                vstatus, vdir, vfname = videoControl.open()
                if vstatus == True:
                    self.controller.video_dir = vdir
                    self.video_filename = os.path.join(vdir, "video", vfname)
                        

            #If user already the the videofilename, update controller and videoControl variables            
            if self.video_filename != None:
                self.controller.update_video(os.path.basename(self.video_filename))
                videoControl.show()
                videoControl.status = True
                self.controller.setVideoMediaObject(videoControl)
                videoControl.setVideoDir(self.controller.video_dir)
                videoControl.setVideoFilename(self.video_filename)
                videoControl.show()
                self.delete_video_button.show()
            
            
    
    def deleteVideo(self):
        global videoControl
        fname = os.path.join(self.controller.video_dir, "video", os.path.basename(self.video_filename))
        print "Removed , ", fname
        os.remove(fname)
        self.controller.update_video("")
        if os.path.isfile(fname):
            if videoControl == None:
                pass
        if videoControl != None:
            videoControl.exitVideo()
            videoControl.close()
        
        self.delete_video_button.hide()
        self.video_filename = None
        self.videoDeleted = True

################################################################################
class QExpandButton(QtGui.QLabel):
    """
    A transparent button type with a + draw in 
    """
    def __init__(self, parent=None):
        """
        QExpandButton(parent: QWidget) -> QExpandButton
        """
        QtGui.QLabel.__init__(self, parent)
        
        self.drawButton(0)
        self.setToolTip('Edit Notes')
        self.setScaledContents(False)
        self.setFrameShape(QtGui.QFrame.NoFrame)

    def sizeHint(self):
        """ sizeHint() -> QSize
        
        """
        return QtCore.QSize(10,10)
        

    def mousePressEvent(self, e):
        """ mousePressEvent(e: QMouseEvent) -> None
        Capture mouse press event on the frame to move the widget
        
        """
        if e.buttons() & QtCore.Qt.LeftButton:
            self.drawButton(1)
    
    def mouseReleaseEvent(self, e):
        self.drawButton(0)
        self.emit(QtCore.SIGNAL('pressed()'))

    def drawButton(self, down):
        """ drawButton(down: bool) -> None
        Custom draw function
        
        """
        self.picture = QtGui.QPicture()
        painter = QtGui.QPainter()
        painter.begin(self.picture)
        painter.setRenderHints(QtGui.QPainter.Antialiasing, False)
        pen = QtGui.QPen(QtCore.Qt.SolidLine)
        pen.setWidth(1)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        brush = QtGui.QBrush(QtCore.Qt.NoBrush)
        if (down):
            pen.setColor(QtGui.QColor(150,150,150,150))
        else:
            pen.setColor(QtGui.QColor(0,0,0,255))

        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawRect(0,0,8,8)
        painter.drawLine(QtCore.QLine(4,2,4,6))
        painter.drawLine(QtCore.QLine(2,4,6,4))
        painter.end()
        self.setPicture(self.picture)

###############################################################################
class QOpenVideo(QExpandButton):
    def __init__(self):
        QExpandButton.__init__(self)
        self.setToolTip('Open Video Player')

################################################################################
class QOpenMultimediaButton(QExpandButton):
    def __init__(self):
        QExpandButton.__init__(self)
        self.setToolTip('Open Audio File')

class QPlayButton(QExpandButton):
    """
    QPlayButton(parent: QExpandButton) -> QPlayButton
    """
    def __init__(self):
        QExpandButton.__init__(self)
        self.setToolTip('Play Audio')
        
    
    
    def drawButton(self, down):
        """ drawButton(down: bool) -> None
        Custom draw function
        
        """
        self.picture = QtGui.QPicture()
        painter = QtGui.QPainter()
        painter.begin(self.picture)
        painter.setRenderHints(QtGui.QPainter.Antialiasing, False)
        pen = QtGui.QPen(QtCore.Qt.SolidLine)
        pen.setWidth(1)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        brush = QtGui.QBrush(QtCore.Qt.NoBrush)
        if(down):
            pen.setColor(QtGui.QColor(150, 150, 150, 150))
        else:
            pen.setColor(QtGui.QColor(0,0,0,255))
            
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawRect(0,0,8,8)
        painter.drawLine(QtCore.QLine(4,2,6,4))
        painter.drawLine(QtCore.QLine(4,6,6,4))
        painter.end()
        self.setPicture(self.picture)

################################################################################
class QDeleteButton(QExpandButton):
    """
    QDeleteButton(parent: QExpandButton) -> QDeleteButton
    """
    def __init__(self):
        QExpandButton.__init__(self)
        self.setToolTip('Delete Audio')

    
    def drawButton(self, down):
        """ drawButton(down: bool) -> None
        Custom draw function
        
        """
        self.picture = QtGui.QPicture()
        painter = QtGui.QPainter()
        painter.begin(self.picture)
        painter.setRenderHints(QtGui.QPainter.Antialiasing, False)
        pen = QtGui.QPen(QtCore.Qt.SolidLine)
        pen.setWidth(1)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        brush = QtGui.QBrush(QtCore.Qt.NoBrush)
        if (down):
            pen.setColor(QtGui.QColor(150,150,150,150))
        else:
            pen.setColor(QtGui.QColor(0,0,0,255))

        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawRect(0,0,8,8)
        painter.drawLine(QtCore.QLine(3,3,6,6))
        painter.drawLine(QtCore.QLine(3,6,6,3))
        painter.end()
        self.setPicture(self.picture)

class QDeleteVideoButton(QDeleteButton):
    """
    QDeleteDeleteButton(parent: QDeleteButton) -> QDeleteVideoButton
    """
    def __init__(self):
        QDeleteButton.__init__(self)
        self.setToolTip('Delete Video')

class QStopButton(QExpandButton):
    """
    QStopButton(parent: QExpandButton) -> QStopButton
    """
    def __init__(self):
        QExpandButton.__init__(self)
        self.setToolTip('Stop Audio')

    
    def drawButton(self, down):
        """ drawButton(down: bool) -> None
        Custom draw function
        
        """
        self.picture = QtGui.QPicture()
        painter = QtGui.QPainter()
        painter.begin(self.picture)
        painter.setRenderHints(QtGui.QPainter.Antialiasing, False)
        pen = QtGui.QPen(QtCore.Qt.SolidLine)
        pen.setWidth(1)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        brush = QtGui.QBrush(QtCore.Qt.NoBrush)
        if (down):
            pen.setColor(QtGui.QColor(150,150,150,150))
        else:
            pen.setColor(QtGui.QColor(0,0,0,255))

        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawRect(0,0,8,8)
        painter.drawLine(QtCore.QLine(3,2,3,6))
        painter.drawLine(QtCore.QLine(6,2,6,6))
        painter.drawLine(QtCore.QLine(3,6,6,6))
        painter.drawLine(QtCore.QLine(3,2,6,2))
        painter.end()
        self.setPicture(self.picture)

class QPauseButton(QExpandButton):
    """
    QPauseButton(parent: QExpandButton) -> QPauseButton
    """
    def __init__(self):
        QExpandButton.__init__(self)
        self.setToolTip('Pause Audio')

    
    def drawButton(self, down):
        """ drawButton(down: bool) -> None
        Custom draw function
        
        """
        self.picture = QtGui.QPicture()
        painter = QtGui.QPainter()
        painter.begin(self.picture)
        painter.setRenderHints(QtGui.QPainter.Antialiasing, False)
        pen = QtGui.QPen(QtCore.Qt.SolidLine)
        pen.setWidth(1)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        brush = QtGui.QBrush(QtCore.Qt.NoBrush)
        if (down):
            pen.setColor(QtGui.QColor(150,150,150,150))
        else:
            pen.setColor(QtGui.QColor(0,0,0,255))

        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawRect(0,0,8,8)
        painter.drawLine(QtCore.QLine(3,2,3,6))
        painter.drawLine(QtCore.QLine(6,2,6,6))
        painter.end()
        self.setPicture(self.picture)
    





################################################################################
class QNotesDialog(QtGui.QDialog):
    """
    A small non-modal dialog with text entry to modify and view notes

    """
    def __init__(self, parent=None):
        """
        QNotesDialog(parent: QWidget) -> QNotesDialog

        """
        QtGui.QDialog.__init__(self, parent)
        self.setModal(False)
        self.notes = QVersionNotes(self)
        self.notes.update_on_focus_out = False
        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.notes)
        layout.setMargin(0)

        self.apply_button = QtGui.QPushButton('Apply', self)
        self.apply_button.setDefault(False)
        self.apply_button.setAutoDefault(False)
        self.ok_button = QtGui.QPushButton('Ok', self)
        self.ok_button.setDefault(False)
        self.ok_button.setAutoDefault(False)
        self.cancel_button = QtGui.QPushButton('Cancel', self)
        self.cancel_button.setDefault(False)
        self.cancel_button.setAutoDefault(False)
        self.buttonLayout = QtGui.QHBoxLayout()
        layout.addLayout(self.buttonLayout)
        self.buttonLayout.addWidget(self.apply_button)
        self.buttonLayout.addWidget(self.ok_button)
        self.buttonLayout.addWidget(self.cancel_button)

        self.setLayout(layout)
        self.controller = None

        QtCore.QObject.connect(self.apply_button,
                               QtCore.SIGNAL("released()"),
                               self.apply_pressed)

        QtCore.QObject.connect(self.ok_button,
                               QtCore.SIGNAL("released()"),
                               self.ok_pressed)

        QtCore.QObject.connect(self.cancel_button,
                               QtCore.SIGNAL("released()"),
                               self.cancel_pressed)
    def apply_pressed(self):
        """ apply_pressed() -> None

        """
        self.notes.commit_changes()

    def ok_pressed(self):
        """ ok_pressed() -> None
        
        """
        self.notes.commit_changes()
        self.close()

    def cancel_pressed(self):
        """ cancel_pressed() -> None
        
        """
        self.notes.reset_changes()
        self.close()

    def updateController(self, controller):
        """ updateController(controller: VistrailController) -> None

        """
        self.controller = controller
        self.notes.controller = controller

    def updateVersion(self, versionNumber):
        """ updateVersion(versionNumber: int) -> None

        """
        self.notes.updateVersion(versionNumber)
        if self.controller:
            if self.controller.vistrail.actionMap.has_key(versionNumber):
                name = self.controller.vistrail.getVersionName(versionNumber)
                title = QtCore.QString("Notes: "+name)
                self.setWindowTitle(title)
            else:
                self.setWindowTitle("Notes")

    def sizeHint(self):
        """ sizeHint() -> QSize
        
        """
        return QtCore.QSize(250,200)
        
################################################################################
class QVersionEmbed(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.versionNumber = None
        lfont = QtGui.QFont("Lucida Grande", 11)
        label1 = QtGui.QLabel("Embed as:")
        label1.setFont(lfont)
        self.cbtype = QtGui.QComboBox()
        self.cbtype.setFont(lfont)
        self.cbtype.setEditable(False)
        items = QtCore.QStringList()
        items << "Wiki" << "Latex";  
        self.cbtype.addItems(items)
    
        self.controller = None
        self.wikitag = '<vistrail host="%s" db="%s" vtid="%s" version="%s" \
tag="%s" showspreadsheetonly="True"/>'
        self.latextag = '\\vistrails[host=%s,\ndb=%s,\nvtid=%s,\nversion=%s,\
\ntag=%s,\nshowspreadsheetonly]{}'
        self.embededt = QtGui.QLineEdit(self)
        self.embededt.setReadOnly(True)
        self.copylabel = QtGui.QLabel('<a href="copy">Copy to Clipboard</a>')
        self.copylabel.setFont(lfont)
        layout = QtGui.QGridLayout()
        layout.addWidget(label1,0,0)
        layout.addWidget(self.cbtype,0,1)
        layout.addWidget(self.copylabel,0,2,QtCore.Qt.AlignRight)
        layout.addWidget(self.embededt,1,0,2,-1)
        self.setLayout(layout)
        
        #connect signals
        self.connect(self.cbtype,
                     QtCore.SIGNAL("currentIndexChanged(const QString &)"),
                     self.change_embed_type)
        
        self.connect(self.copylabel,
                     QtCore.SIGNAL("linkActivated(const QString &)"),
                     self.copy_to_clipboard)

    def check_version(self):
        """check_version() -> bool
        Only vistrails on a database are allowed to embed a tag"""
        result = False
        if self.controller:
            if self.controller.locator:
                if hasattr(self.controller.locator,'host'):
                    result = True
        return result

    def check_controller_status(self):
        """check_controller_status() -> bool
        this checks if the controller has saved the latest changes """
        result = False
        if self.controller:
            result = not self.controller.changed
        return result
    
    def updateEmbedText(self):
        ok = (self.check_version() and self.check_controller_status() and
              self.versionNumber > 0)
        self.embededt.setEnabled(ok)
        self.copylabel.setEnabled(ok)
        self.embededt.setText('')
        if self.controller and self.versionNumber > 0:
            if self.controller.locator and not self.controller.changed:
                loc = self.controller.locator
                try:
                    if self.cbtype.currentText() == "Wiki":
                        tag = self.wikitag
                    elif self.cbtype.currentText() == "Latex":
                        tag = self.latextag
                    versiontag = \
                        self.controller.vistrail.getVersionName(self.versionNumber)
                        
                    tag = tag % (loc.host,
                                 loc.db,
                                 loc.obj_id,
                                 self.versionNumber,
                                 versiontag)
                    
                    self.embededt.setText(tag)
                    return
                except Exception, e:
                    self.embededt.setText('')
            elif self.controller.changed:
                self.embededt.setText('Please, save your vistrails first')
            else:
                self.embededt.setText('')
                
    def updateVersion(self, versionNumber):
        self.versionNumber = versionNumber
        self.updateEmbedText()

    def copy_to_clipboard(self):
        clipboard = QtGui.QApplication.clipboard()
        clipboard.setText(self.embededt.text())
    
    def change_embed_type(self, text):
        self.updateEmbedText()    
