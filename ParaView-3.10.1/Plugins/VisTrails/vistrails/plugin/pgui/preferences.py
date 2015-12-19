
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
from PyQt4 import QtGui, QtCore
from gui.utils import getBuilderWindow
import CaptureAPI

class QPluginPreferencesDialog(QtGui.QDialog):
    """ Build the GUI for Preferences class """
    
    def __init__(self, parent=None):
        """ Construct a simple dialog layout """
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle('Provenance Explorer Preferences')
        layout = QtGui.QVBoxLayout(self)
        self.setLayout(layout)

        # vistrails window always on top
        self.alwaysOnTopCB = QtGui.QCheckBox('Plug-in window always on top')
        state = CaptureAPI.getPreference('VisTrailsAlwaysOnTop')
        if state is not None:
            state = int(CaptureAPI.getPreference('VisTrailsAlwaysOnTop'))
            if state:
                self.alwaysOnTopCB.setCheckState(QtCore.Qt.Checked)
            else:
                self.alwaysOnTopCB.setCheckState(QtCore.Qt.Unchecked)
            layout.addWidget(self.alwaysOnTopCB)

        # The number of visible versions edit box
        self.numberOfVisibleVersionsSB = QtGui.QSpinBox()
        if CaptureAPI.getPreference('VisTrailsNumberOfVisibleVersions') is not None:
            novLayout = QtGui.QHBoxLayout()
            layout.addLayout(novLayout)
            novLayout.setMargin(0)

            novLabel = QtGui.QLabel('Number of recent versions visible')
            novLayout.addWidget(novLabel)
        
            novLayout.addWidget(self.numberOfVisibleVersionsSB)
            self.numberOfVisibleVersionsSB.setRange(0, 1000)
            self.numberOfVisibleVersionsSB.setValue(
              int(CaptureAPI.getPreference('VisTrailsNumberOfVisibleVersions')))
            novLayout.addStretch()

        # Enabling snapshots
        self.snapShotCB = QtGui.QCheckBox('Take state snapshots')
        self.numSnapshotTB= QtGui.QSpinBox()
        state = CaptureAPI.getPreference('VisTrailsSnapshotEnabled')
        if state is not None:
            layout.addSpacing(10)
            state = int(CaptureAPI.getPreference('VisTrailsSnapshotEnabled'))
            if state:
                self.snapShotCB.setCheckState(QtCore.Qt.Checked)
            else:
                self.snapShotCB.setCheckState(QtCore.Qt.Unchecked)
            layout.addWidget(self.snapShotCB)
            self.connect(self.snapShotCB,
                         QtCore.SIGNAL('clicked()'),
                         self.updateState)

            # The number of actions before a snapshot     
            if CaptureAPI.getPreference('VisTrailsSnapshotCount') is not None:
                nosLayout = QtGui.QHBoxLayout()
                layout.addLayout(nosLayout)
                nosLayout.setMargin(0)

                nosLabel = QtGui.QLabel('Number of actions between snapshots')
                nosLayout.addWidget(nosLabel)
        
                nosLayout.addWidget(self.numSnapshotTB)
                self.numSnapshotTB.setRange(0,1000)
                self.numSnapshotTB.setValue(
                        int(CaptureAPI.getPreference('VisTrailsSnapshotCount')))
                self.numSnapshotTB.setEnabled(state)
                nosLayout.addStretch()            

        # Enabling Autosave
        self.autosaveCB = QtGui.QCheckBox('Autosave')
        self.autosaveDelayTB= QtGui.QSpinBox()
        state = CaptureAPI.getPreference('VisTrailsAutosaveEnabled')
        if state is not None:
            layout.addSpacing(10)
            state = int(CaptureAPI.getPreference('VisTrailsAutosaveEnabled'))
            if state:
                self.autosaveCB.setCheckState(QtCore.Qt.Checked)
            else:
                self.autosaveCB.setCheckState(QtCore.Qt.Unchecked)
            layout.addWidget(self.autosaveCB)
            self.connect(self.autosaveCB,
                         QtCore.SIGNAL('clicked()'),
                         self.updateState)

            # The delay in minutes between autosaves
            if CaptureAPI.getPreference('VisTrailsAutosaveDelay') is not None:
                adLayout = QtGui.QHBoxLayout()
                layout.addLayout(adLayout)
                adLayout.setMargin(0)

                adLabel = QtGui.QLabel('Minutes between autosave')
                adLayout.addWidget(adLabel)
        
                adLayout.addWidget(self.autosaveDelayTB)
                self.autosaveDelayTB.setRange(1,100)
                self.autosaveDelayTB.setValue(
                     int(CaptureAPI.getPreference('VisTrailsAutosaveDelay')))
                self.autosaveDelayTB.setEnabled(state)
                adLayout.addStretch()


        # Store files in vt
        self.fileStoreCB = QtGui.QCheckBox('Store opened and imported files in vistrail')
        if CaptureAPI.getPreference('VisTrailsStoreFiles') is not None:
            layout.addSpacing(10)
            state = int(CaptureAPI.getPreference('VisTrailsStoreFiles'))
            if state:
                self.fileStoreCB.setCheckState(QtCore.Qt.Checked)
            else:
                self.fileStoreCB.setCheckState(QtCore.Qt.Unchecked)
            layout.addWidget(self.fileStoreCB)

        # A space
        layout.addSpacing(10)
        layout.addStretch()

        # Then the buttons
        bLayout = QtGui.QHBoxLayout()
        layout.addLayout(bLayout)
        bLayout.addStretch()

        self.saveButton = QtGui.QPushButton('Save')
        bLayout.addWidget(self.saveButton)
        
        self.cancelButton = QtGui.QPushButton('Cancel')
        bLayout.addWidget(self.cancelButton)
        bLayout.addStretch()

        # Connect buttons to dialog handlers
        self.connect(self.saveButton, QtCore.SIGNAL('clicked()'),
                     self.accept)
        self.connect(self.cancelButton, QtCore.SIGNAL('clicked()'),
                     self.reject)

        controller = getBuilderWindow().viewManager.currentWidget().controller
        controller.set_num_versions_always_shown(self.numberOfVisibleVersionsSB.value())
        
        # Reader specific GUI
        if CaptureAPI.isReadOnly():
            self.autosaveCB.setText('Autosave (Pro)')
            self.autosaveCB.setEnabled(False)
            adLabel.setText('Minutes between autosave (Pro)')
            adLabel.setEnabled(False)
            self.autosaveDelayTB.setEnabled(False)
            self.fileStoreCB.setText('Store opened and imported files in vistrail (Pro)')
            self.fileStoreCB.setEnabled(False)
            self.snapShotCB.setText('Take state snapshots (Pro)')
            self.snapShotCB.setEnabled(False)
            nosLabel.setText('Number of actions between snapshots (Pro)')
            nosLabel.setEnabled(False)
            self.numSnapshotTB.setEnabled(False)

    def updateState(self):
        self.numSnapshotTB.setEnabled(self.snapShotCB.checkState() == QtCore.Qt.Checked)
        self.autosaveDelayTB.setEnabled(self.autosaveCB.checkState() == QtCore.Qt.Checked)

    def sizeHint(self):
        return QtCore.QSize(384, 128)

    def accept(self):
        """ Need to save the preferences """
        QtGui.QDialog.accept(self)
        self.savePreferences()

    def savePreferences(self):
        """ Map all widget values back to App Preferences """
        num_versions = self.numberOfVisibleVersionsSB.value()
        num_snapshot = self.numSnapshotTB.value()
        snap_enabled = 1
        if self.snapShotCB.checkState() == QtCore.Qt.Unchecked:
            snap_enabled = 0
        file_store = 1
        if self.fileStoreCB.checkState() == QtCore.Qt.Unchecked:
            file_store = 0
        autosave_enabled = 1
        if self.autosaveCB.checkState() == QtCore.Qt.Unchecked:
            autosave_enabled = 0
        autosave_delay = self.autosaveDelayTB.value()

        if self.alwaysOnTopCB.checkState() == QtCore.Qt.Unchecked:
            getBuilderWindow().setWindowFlags(getBuilderWindow().windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
            getBuilderWindow().show()
            always_on_top = 0
        else:
            getBuilderWindow().setWindowFlags(getBuilderWindow().windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            getBuilderWindow().show()
            always_on_top = 1

        controller = getBuilderWindow().viewManager.currentWidget().controller
        controller.set_num_versions_always_shown(num_versions)

        reset_autosave = (autosave_enabled != int(CaptureAPI.getPreference('VisTrailsAutosaveEnabled')) or \
                              autosave_delay != int(CaptureAPI.getPreference('VisTrailsAutosaveDelay')))

        if CaptureAPI.getPreference('VisTrailsNumberOfVisibleVersions') is not None:
            CaptureAPI.setPreference('VisTrailsNumberOfVisibleVersions',
                                     str(num_versions))
        if CaptureAPI.getPreference('VisTrailsSnapshotCount') is not None:
            CaptureAPI.setPreference('VisTrailsSnapshotCount',
                                     str(num_snapshot))
        if CaptureAPI.getPreference('VisTrailsSnapshotEnabled') is not None:
            CaptureAPI.setPreference('VisTrailsSnapshotEnabled',
                                     str(snap_enabled))
        if CaptureAPI.getPreference('VisTrailsAutosaveEnabled') is not None:
            CaptureAPI.setPreference('VisTrailsAutosaveEnabled',
                                     str(autosave_enabled))
        if CaptureAPI.getPreference('VisTrailsAutosaveDelay') is not None:
            CaptureAPI.setPreference('VisTrailsAutosaveDelay',
                                     str(autosave_delay))
        if CaptureAPI.getPreference('VisTrailsStoreFiles') is not None:
            CaptureAPI.setPreference('VisTrailsStoreFiles',
                                     str(file_store))
        if CaptureAPI.getPreference('VisTrailsAlwaysOnTop') is not None:
            CaptureAPI.setPreference('VisTrailsAlwaysOnTop',
                                     str(always_on_top))
        
        if reset_autosave:
            controller.reset_autosave_timer()
        try:
            CaptureAPI.savePreferences()
        except:
            print "Warning: could not save preferences"
