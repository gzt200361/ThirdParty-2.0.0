
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

import sys
import os
import tempfile
import time
import shutil
from PyQt4 import QtCore, QtGui
from PyQt4.phonon import Phonon


################################################################################
#Video Widget
###############################################################################

class VideoMainWindow(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('Video Player')
        self.resize(300,300)
        self.filename = None
        self.videoDir = None
        self.videofname = None
        self.mediaObject = None
        self.videoWidget = None
        self.audioOutput = None
        self.layout = None
        self.PhononVW = None
        self.PhononAO = None
        self.setCurrentSrc = None
        self.status = True
        self.buildPlayerWindow()

    def buildPlayerWindow(self):
        play = QtGui.QPushButton('Play')
        pause = QtGui.QPushButton('Pause')
        stop = QtGui.QPushButton('Stop')
        exitVideo = QtGui.QPushButton('Close')
        
        if self.layout == None:
            self.layout = QtGui.QVBoxLayout()
        
        self.mediaObject = Phonon.MediaObject()
        self.videoWidget = Phonon.VideoWidget()
        self.audioOutput = Phonon.AudioOutput(Phonon.VideoCategory)

        self.layout.addWidget(self.videoWidget)           
        self.control = QtGui.QHBoxLayout()
        self.control.setAlignment(QtCore.Qt.AlignHCenter)
        self.control.addSpacing(2)
        self.control.addWidget(play)
        self.control.addWidget(pause)
        self.control.addWidget(stop)
        self.control.addWidget(exitVideo)
        
        self.layout.addLayout(self.control)
        
        self.setLayout(self.layout)

        self.setPosition()
        
        QtCore.QObject.connect(play,
                               QtCore.SIGNAL("clicked()"),
                               self.playVideo)

        
        QtCore.QObject.connect(pause,
                               QtCore.SIGNAL("clicked()"),
                               self.pauseVideo)

        QtCore.QObject.connect(stop,
                               QtCore.SIGNAL("clicked()"),
                               self.stopVideo)


        QtCore.QObject.connect(exitVideo,
                               QtCore.SIGNAL('clicked()'),
                               self.exitVideo)

        
    def setPosition(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width()-size.width())/1.1, (screen.height()-size.height())/1.2)
        
    def open(self):
        self.filename = QtGui.QFileDialog.getOpenFileName(self, 'Open File', 
                                                          '/', "Music (*.3g2 *.3gp *.amv *.asf *.asx *.avi *wmv *.vob *.wwf *.rm *.mpg *.mov *.flv *.mp4)")

        self.status = True
        
        #If user clicked on the Cancel button in the FileDialog box set status variable to False
        if self.filename == "":
            self.status = False
            self.videoDir = None
            self.videofname = None
            return self.status, self.videoDir, self.videofname
            
        else:
            #If the video dir was already created, dump the files in that video dir
            if self.videoDir:
                filename = self.filename
                bname = os.path.basename(str(filename))
                fbasename, fextension = os.path.splitext(bname)
            
                #Create temp file
                tmp_dir = os.path.join(self.videoDir, "video")

                fd, temp_fname = tempfile.mkstemp(suffix=fextension, prefix="VTVideo", dir=tmp_dir)
                os.close(fd)
                shutil.copyfile(filename, temp_fname)
                self.video_filename = temp_fname
                self.videofname = os.path.basename(temp_fname)

            #If the video dir has not been created
            else:
                if self.videoDir == None:
                    self.videoDir = tempfile.mkdtemp(prefix="VTVideo")
                else:
                    pass
            
                tmp_dir = os.path.join(self.videoDir, "video")
                
                if os.path.isdir(tmp_dir) == True:
                    pass
                else:
                    os.mkdir(os.path.join(self.videoDir, "video"))
                    filename = self.filename
                    bname = os.path.basename(str(filename))
                    fbasename, fextension = os.path.splitext(bname)
                    
                    #Create temp file
                    fd, temp_fname = tempfile.mkstemp(suffix=fextension, prefix="VTVideo", dir=tmp_dir) 
                    os.close(fd)
                    shutil.copyfile(filename, temp_fname)
                    self.video_filename = temp_fname
                    self.videofname = os.path.basename(temp_fname)
            
            #If video filename is not set, just return the video dir
            if self.videofname == None:
                return self.videoDir

            #Else return everything, including status of video dialog
            else:
                return self.status, self.videoDir, self.videofname


    def setCurrentSource(self):
        if self.videofname != None:
            self.setCurrentSrc = self.mediaObject.setCurrentSource(Phonon.MediaSource(QtCore.QUrl.fromLocalFile(os.path.join(self.videoDir, "video", self.videofname))))
            
        elif self.filename != None:
            self.setCurrentSrc = self.mediaObject.setCurrentSource(Phonon.MediaSource(QtCore.QUrl.fromLocalFile(os.path.join(self.videoDir, "video", self.filename))))

            
    def createPath(self):
        if self.mediaObject != None and self.videoWidget:
            self.PhononVW = Phonon.createPath(self.mediaObject, self.videoWidget)
            self.PhononAO = Phonon.createPath(self.mediaObject, self.audioOutput)

    def playVideo(self):
        if self.PhononVW == None and self.PhononAO == None:
            self.createPath()
        self.setCurrentSource()
        if self.mediaObject.currentTime() == self.mediaObject.totalTime() and self.mediaObject.currentTime() != 0 and self.mediaObject.totalTime() != 0:
            self.mediaObject.stop()
        
            
        self.mediaObject.play()

    def pauseVideo(self):
        self.mediaObject.pause()

    def stopVideo(self):
        self.mediaObject.stop()

    def exitVideo(self):
        if self.mediaObject.currentTime() != 0:
            self.mediaObject.stop()
        self.close()

    def setVideoDir(self, vdir):
        self.videoDir = vdir

    def setVideoFilename(self, fname):
        self.filename = fname

    def setVideoName(self, vname):
        self.videofname = vname

    def setStatus(self, status):
        self.status = status

    def resetCurrentSource(self):
        self.mediaObject.setCurrentSource(Phonon.MediaSource(QtCore.QUrl.fromLocalFile("")))
