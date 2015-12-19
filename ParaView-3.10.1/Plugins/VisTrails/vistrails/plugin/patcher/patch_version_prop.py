
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
## Copyright (C) 2008, 2009 VisTrails, Inc. All rights reserved.
##
############################################################################

##############################################################################
# Patch QVersionPropOverlay

import os
from PyQt4 import QtCore, QtGui
from PyQt4.phonon import Phonon
import gui.version_prop

def QVPO_updateVersion(self, versionNumber):
    """ updateVersion(versionNumber: int) -> None
    Update the text items
    
    """
    self.notes_dialog.updateVersion(versionNumber)
    if self.controller:
        import CaptureAPI
        if self.controller.vistrail.actionMap.has_key(versionNumber) and \
                not self.controller.vistrail.actionMap[versionNumber].prune:
            action = self.controller.vistrail.actionMap[versionNumber]
            name = self.controller.vistrail.getVersionName(versionNumber)
            description = self.controller.vistrail.get_description(versionNumber)
            details = self.controller.vistrail.get_details(versionNumber)
            self.tag.setText(self.truncate(QtCore.QString(name)))
            self.tag.setToolTip(QtCore.QString(name))
            self.description.setText(self.truncate(QtCore.QString(description)))
            self.description.setToolTip(QtCore.QString(description))
            self.user.setText(self.truncate(QtCore.QString(action.user)))
            self.user.setToolTip(QtCore.QString(action.user))
            self.date.setText(self.truncate(QtCore.QString(action.date)))
            self.date.setToolTip(QtCore.QString(action.date))
            if action.notes:
                s = self.convertHtmlToText(QtCore.QString(action.notes))
                self.notes.setText(self.truncate(s))
                self.notes.setToolTip(action.notes)
            else:
                self.notes.setText('')
                self.notes.setToolTip('')
            self.notes_button.show()
            self.open_audio_button.show()
            self.open_video_button.show()
            self.audio_filename = action.audio
            self.video_filename = action.video
            if self.video_filename != None:
                self.delete_video_button.show()
                if self.controller.videoMediaObject != None:
                    if self.controller.videoMediaObject.mediaObject.currentTime() != 0:
                        self.controller.videoMediaObject.stopVideo()
                    self.controller.videoMediaObject.setVideoName(self.video_filename)
                    self.controller.videoMediaObject.setVideoDir(self.controller.video_dir)
                    self.controller.videoMediaObject.exitVideo()
                    
                             
            else:
                self.delete_video_button.hide()
                if self.controller.videoMediaObject != None:
                    if self.controller.videoMediaObject.mediaObject.currentTime() != 0:
                        self.controller.videoMediaObject.stopVideo()
                    self.controller.videoMediaObject.exitVideo()
            if self.audio_filename != None:
                self.play_audio_button.show()
                self.pause_audio_button.show()
                self.stop_audio_button.show()
                self.delete_audio_button.show()
                if self.controller.audioMediaObject != None: 
                    self.loadPhonon()
                    self.loadAudio()
            else:
                if self.controller.audioMediaObject != None:
                    self.controller.audioMediaObject.stop()
                self.play_audio_button.hide()
                self.pause_audio_button.hide()
                self.stop_audio_button.hide()
                self.delete_audio_button.hide()
            if self.controller.videoMediaObject != None:
                if self.controller.videoMediaObject.filename == None:
                    self.delete_video_button.hide()
                    if self.controller.videoMediaObject.mediaObject.currentTime() != 0:
                        self.controller.videoMediaObject.stopVideo()
                    self.controller.videoMediaObject.exitVideo()
                
            
            self.details.setText(self.truncate(QtCore.QString(details)))
            self.details.setToolTip(QtCore.QString(details))
        else:
            self.tag.setText('')
            self.tag.setToolTip('')
            self.description.setText('')
            self.description.setToolTip('')
            self.user.setText('')
            self.user.setToolTip('')
            self.date.setText('')
            self.date.setToolTip('')
            self.notes.setText('')
            self.notes.setToolTip('')
            self.play_audio_button.hide()
            self.pause_audio_button.hide()
            self.stop_audio_button.hide()
            self.open_audio_button.hide()
            self.delete_audio_button.hide()
            self.open_video_button.hide()
            self.delete_video_button.hide()
            if self.controller.videoMediaObject != None:
                if self.controller.videoMediaObject.mediaObject.currentTime() != 0:
                    self.controller.videoMediaObject.stopVideo()
                self.controller.videoMediaObject.exitVideo()
            self.notes_button.hide()
            self.details.setText('')
            self.details.setToolTip('')
            self.audio_filename = None
            self.video_filename = None

gui.version_prop.QVersionPropOverlay.updateVersion = QVPO_updateVersion
