
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
from gui.builder_window import QBuilderWindow
from gui.theme import CurrentTheme
from gui.vistrail_toolbar import QVistrailInteractionToolBar
from plugin.pgui.search_toolbar import QSearchToolBar
from plugin.pgui.playback_toolbar import QPlaybackToolBar
from plugin.pgui.preferences import QPluginPreferencesDialog
from plugin.pgui.common_widgets import QMessageDialog
from plugin.pgui.common_widgets import MessageDialogContainer
from core.db.locator import FileLocator, untitled_locator
from plugin.pcore.patch import PluginPatch
import core.system
import CaptureAPI

class QPluginOperationEvent(QtCore.QEvent):
    """
    QPluginOperationEvent is used to send action changes from the plugin to the
    builder window in a thread-safe manner

    """
    eventType = QtCore.QEvent.Type(QtCore.QEvent.User)
    def __init__(self, name, details, snapshot, operations, fromVersion):
        """ QPluginOperationEvent()
        """
        QtCore.QEvent.__init__(self, self.eventType)
        self.name = name
        self.details = details
        self.snapshot = snapshot
        self.operations = operations
        self.fromVersion = fromVersion

class QPluginBuilderWindow(QBuilderWindow):
    def __init__(self, parent=None):
        QBuilderWindow.__init__(self, parent)
        self.descriptionWidget = QtGui.QLabel()
        self.progressLabel = QtGui.QLabel()
        self.progressLabel.setMaximumWidth(80)
        self.progressLabel.setMinimumWidth(80)
        self.progressWidget = QtGui.QProgressBar()
        self.progressWidget.setRange(0,100)
        self.statusBar().addWidget(self.descriptionWidget,1)
        self.statusBar().addWidget(self.progressLabel,1)
        self.statusBar().addWidget(self.progressWidget,1)
        self.statusWarning = None
        self.descriptionWidget.hide()
        self.progressLabel.hide()
        self.progressWidget.hide()

        self.title = CaptureAPI.getPluginTitle()
        self.setWindowTitle(self.title)
        self.setWindowIcon(CurrentTheme.APPLICATION_ICON)
        #self.modulePalette.toolWindow().destroy()
        self.updateApp = False
        self.timeStatsWindow = None

        if core.system.systemType in ['Darwin']:
            self.menuBar().setAttribute(QtCore.Qt.WA_MacSmallSize)
            self.menuBar().setAttribute(QtCore.Qt.WA_MacMetalStyle)

        self.searchToolBar = QSearchToolBar(self)
        self.addToolBar(QtCore.Qt.BottomToolBarArea, self.searchToolBar)

        self.addToolBarBreak(QtCore.Qt.BottomToolBarArea)

        self.playbackToolBar = QPlaybackToolBar(self)
        self.addToolBar(QtCore.Qt.BottomToolBarArea, self.playbackToolBar)

        self.addonToolBar.addAction(self.keepViewAction)
        self.addonToolBar.addAction(self.searchToolBar.toggleViewAction())
        self.addonToolBar.addAction(self.playbackToolBar.toggleViewAction())

        self.toolsMenu.addSeparator()
        self.toolsMenu.addAction(self.searchToolBar.toggleViewAction())
        self.toolsMenu.addAction(self.playbackToolBar.toggleViewAction())

        self.interactionToolBar._selectCursorAction.setToolTip('Select')
        self.interactionToolBar._selectCursorAction.setStatusTip('Select versions and edit the tree view')
        self.interactionToolBar._panCursorAction.setToolTip('Pan')
        self.interactionToolBar._panCursorAction.setStatusTip('Pan the tree view (Shift + Click)')
        self.interactionToolBar._zoomCursorAction.setToolTip('Zoom')
        self.interactionToolBar._zoomCursorAction.setStatusTip('Zoom the tree view (Ctrl + Click)')

        self.connect(self.viewManager,
                     QtCore.SIGNAL('currentVistrailChanged'),
                     self.updateAddonToolBar)

        geometry = CaptureAPI.getPreference('VisTrailsBuilderWindowGeometry')
        if geometry!='':
            self.restoreGeometry(QtCore.QByteArray.fromBase64(QtCore.QByteArray(geometry)))
            desktop = QtGui.QDesktopWidget()
            if desktop.screenNumber(self)==-1:
                self.move(desktop.screenGeometry().topLeft())

        alwaysOnTop = int(CaptureAPI.getPreference('VisTrailsAlwaysOnTop'))
        if alwaysOnTop:
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

    def create_first_vistrail(self):
        """ create_first_vistrail() -> None

        """
        # FIXME: when interactive and non-interactive modes are separated,
        # this autosave code can move to the viewManager
        if not self.dbDefault and untitled_locator().has_temporaries():
            if not FileLocator().prompt_autosave(self):
                untitled_locator().clean_temporaries()

        if self.viewManager.newVistrail(True, False):
            self.viewModeChanged(1)
        self.viewManager.set_first_view(self.viewManager.currentView())
        
        # Pre-compute default values for existing nodes in a new scene
        controller = self.viewManager.currentWidget().controller
        controller.store_preset_attributes()
        controller.change_selected_version(0)
        self.connect(controller,
                     QtCore.SIGNAL('versionWasChanged'),
                     self.versionSelectionChange)

        self.updateAddonToolBar(self.viewManager.currentWidget())
        
        if CaptureAPI.isReadOnly():
            self.viewManager.currentWidget().hide()
            self.addonToolBar.setEnabled(False)
            self.interactionToolBar.setEnabled(False)
            self.editMenu.setEnabled(False)
            self.toolsMenu.setEnabled(False)
            self.viewMenu.setEnabled(False)
            self.open_vistrail_default()

    def sizeHint(self):
        """ sizeHint() -> QRect
        Return the recommended size of the builder window

        """
        return QtCore.QSize(400, 600)

    def newVistrail(self):
        """ newVistrail() -> None
        Start a new vistrail

        """

        # may have cancelled the new
        if not QBuilderWindow.newVistrail(self):
            return

        self.viewModeChanged(1)

        # Pre-compute default values for existing nodes in a new scene
        controller = self.viewManager.currentWidget().controller
        controller.store_preset_attributes()
        self.connect(controller,
                     QtCore.SIGNAL('versionWasChanged'),
                     self.versionSelectionChange)
        self.updateAddonToolBar(self.viewManager.currentWidget())
        CaptureAPI.afterNewVistrail()

    def open_vistrail(self, locator_class):
        """ open_vistrail(locator_class: locator) -> None

        """
        QBuilderWindow.open_vistrail(self, locator_class)
        self.updateAddonToolBar(self.viewManager.currentWidget())

    def setUpdateAppEnabled(self, b):
        """ setUpdateAppEnabled(b: bool)
        Enable/Disable updating app when the version change in the
        version tree

        """
        self.updateApp = b

    def changeVersionWithoutUpdatingApp(self, version):
        """ changeVersionWithoutUpdate(version: int)
        Change the current version of the version tree without updating the app

        """
        if version<0:
            version = 0
        b = self.updateApp
        self.setUpdateAppEnabled(False)
        controller = self.viewManager.currentWidget().controller
        if controller:
            controller.change_selected_version(version)
        self.setUpdateAppEnabled(b)

    def addNewVersion(self, name, details, snapshot, ops, fromVersion):
        """ addNewVersion(name: str, details: str, snapshot: int, ops: str, fromVersion: int)
        Post the operation event to self for adding it to the version
        tree. 'fromVersion' indicates where the new version should derive
        from (the value of -1 to indicate the current version).

        """
        QtCore.QCoreApplication.sendEvent(self, QPluginOperationEvent(name, details, snapshot, ops, fromVersion))

    def event(self, e):
        """ event(e: QEvent)
        Parse QPluginOperationEvent and store it to Visrails
        """
        if (e.type()==QPluginOperationEvent.eventType) \
        and (self.viewManager.currentWidget()!=None):
            controller = self.viewManager.currentWidget().controller
            if e.fromVersion>=0:
                self.changeVersionWithoutUpdatingApp(e.fromVersion)
            controller.update_scene_script(e.name, e.details, e.snapshot, e.operations)
            return False
        return QBuilderWindow.event(self, e)

    def createToolBar(self):
        """ createToolBar() -> None
        Create a plugin specific toolbar

        """
        iconSize = 20
        self.toolBar = QtGui.QToolBar(self)
        self.toolBar.setWindowTitle('Basic')
        self.toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.toolBar.setIconSize(QtCore.QSize(iconSize,iconSize))
        self.toolBar.layout().setSpacing(1)

        self.addToolBar(self.toolBar)
        self.toolBar.addAction(self.newVistrailAction)
        self.toolBar.addAction(self.openFileAction)
        self.toolBar.addAction(self.saveFileAction)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.undoAction)
        self.toolBar.addAction(self.redoAction)

        self.addonToolBar = QtGui.QToolBar(self)
        self.addonToolBar.setWindowTitle('Tools')
        self.addonToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.addonToolBar.setIconSize(QtCore.QSize(iconSize,iconSize))
        self.addonToolBar.layout().setSpacing(1)
        self.addToolBar(self.addonToolBar)

        self.interactionToolBar = QVistrailInteractionToolBar(self)
        self.interactionToolBar.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.interactionToolBar.setIconSize(QtCore.QSize(iconSize,iconSize))
        self.interactionToolBar.layout().setSpacing(1)
        self.addToolBar(self.interactionToolBar)

    def createActions(self):
        """ createActions() -> None
        Construct Plug-in specific actions

        """
        QBuilderWindow.createActions(self)

        # Modify Core Actions
        self.redoAction.setShortcuts(['Shift+Z','Ctrl+Y'])
        self.quitVistrailsAction = QtGui.QAction('Quit Plug-In', self)
        self.quitVistrailsAction.setShortcut('Ctrl+Q')
        self.quitVistrailsAction.setStatusTip('Exit Plug-In')
        self.editPreferencesAction.setStatusTip('Edit plug-in preferences')
        self.helpAction = QtGui.QAction(self.tr('About Provenance Explorer...'), self)

        # Create plugin specific actions
        self.keepViewAction = QtGui.QAction(CurrentTheme.VIEW_ON_ICON, 'Lock View', self)
        self.keepViewAction.setEnabled(True)
        self.keepViewAction.setCheckable(True)
        if int(CaptureAPI.getPreference('VisTrailsUseRecordedViews')):
            self.keepViewAction.setChecked(0)
            self.keepViewAction.setIcon(CurrentTheme.VIEW_OFF_ICON)
        else:
            self.keepViewAction.setChecked(1)
        self.keepViewAction.setStatusTip('Lock the current view settings while navigating versions')

        self.expandBranchAction = QtGui.QAction('Expand Branch', self)
        self.expandBranchAction.setEnabled(True)
        self.expandBranchAction.setStatusTip('Expand all versions in the tree below the current version')

        self.collapseBranchAction = QtGui.QAction('Collapse Branch', self)
        self.collapseBranchAction.setEnabled(True)
        self.collapseBranchAction.setStatusTip('Collapse all expanded versions in the tree below the current version')

        self.collapseAllAction = QtGui.QAction('Collapse All', self)
        self.collapseAllAction.setEnabled(True)
        self.collapseAllAction.setStatusTip('Collapse all expanded branches of the tree')

        self.hideBranchAction = QtGui.QAction('Hide Branch', self)
        if core.system.systemType in ['Darwin']:
            self.hideBranchAction.setShortcut('Meta+H')
        else:
            self.hideBranchAction.setShortcut('Ctrl+H')
        self.hideBranchAction.setEnabled(True)
        self.hideBranchAction.setStatusTip('Hide all versions in the tree including and below the current version')

        self.showAllAction = QtGui.QAction('Show All', self)
        self.showAllAction.setEnabled(True)
        self.showAllAction.setStatusTip('Show all hidden versions')

        self.resetViewAction = QtGui.QAction('Frame All', self)
        if core.system.systemType in ['Darwin']:
            self.resetViewAction.setShortcut('Meta+A')
        else:
            self.resetViewAction.setShortcut('A')
        self.resetViewAction.setShortcutContext(QtCore.Qt.WidgetShortcut)
        self.resetViewAction.setStatusTip('Reset tree view to show all versions')

        self.focusViewAction = QtGui.QAction('Frame Selection', self)
        if core.system.systemType in ['Darwin']:
            self.focusViewAction.setShortcut('Meta+F')
        else:
            self.focusViewAction.setShortcut('F')
        self.focusViewAction.setShortcutContext(QtCore.Qt.WidgetShortcut)
        self.focusViewAction.setStatusTip('Reset tree view to show selected version')

        self.timeStatsAllAction = QtGui.QAction('Compute Statistics', self)
        self.timeStatsAllAction.setEnabled(True)
        self.timeStatsAllAction.setStatusTip('Show time statistics for entire version tree')
        
        self.timeStatsAction = QtGui.QAction('Compute Sequence Statistics...', self)
        self.timeStatsAction.setEnabled(True)
        self.timeStatsAction.setStatusTip('Show time statistics between two versions')

        self.snapshotAction = QtGui.QAction('Create Snapshot', self)
        self.snapshotAction.setEnabled(False)
        self.snapshotAction.setStatusTip('Create a new version with the contents of the current scene')

        self.visDiffAction = QtGui.QAction('Compute Visual Difference...', self)
        self.visDiffAction.setEnabled(True)
        self.visDiffAction.setStatusTip('Visually display differences between two versions')

        self.copyOperationAction = QtGui.QAction('Copy', self)
        self.copyOperationAction.setShortcut('Ctrl+C')
        self.copyOperationAction.setEnabled(True)
        self.copyOperationAction.setStatusTip('Copy the selected operation to the clipboard')

        self.copySequenceAction = QtGui.QAction('Copy Sequence...', self)
        self.copySequenceAction.setEnabled(True)
        self.copySequenceAction.setStatusTip('Copy a sequence of operations to the clipboard')

        self.pasteOperationAction = QtGui.QAction('Paste', self)
        self.pasteOperationAction.setShortcut('Ctrl+V')
        self.pasteOperationAction.setEnabled(False)
        self.pasteOperationAction.setStatusTip('Paste operations from the clipboard to selected version')

        # Reader
        if CaptureAPI.isReadOnly():
            self.newVistrailAction.setText('&New (Pro)')
            self.newVistrailAction.setEnabled(False)
            self.saveFileAction.setText('&Save (Pro)')
            self.saveFileAction.setEnabled(False)
            self.saveFileAsAction.setText('Save as... (Pro)')
            self.saveFileAsAction.setEnabled(False)
            self.timeStatsAllAction.setText('Compute Statistics... (Pro)')
            self.timeStatsAllAction.setEnabled(False)
            self.timeStatsAction.setText('Compute Sequence Statistics... (Pro)')
            self.timeStatsAction.setEnabled(False)
            self.snapshotAction.setText('Take Snapshot (Pro)')
            self.snapshotAction.setEnabled(False)
            self.copyOperationAction.setText('Copy (Pro)')
            self.copyOperationAction.setEnabled(False)
            self.copySequenceAction.setText('Copy Sequence... (Pro)')
            self.copySequenceAction.setEnabled(False)
            self.pasteOperationAction.setText('Paste (Pro)')
            self.pasteOperationAction.setEnabled(False)
            self.hideBranchAction.setText('Hide Branch (Pro)')
            self.hideBranchAction.setEnabled(False)
            self.showAllAction.setText('Show All (Pro)')
            self.showAllAction.setEnabled(False)

    def connectSignals(self):
        """ connectSignals() -> None
        Connect Plug-in specific signals

        """
        QBuilderWindow.connectSignals(self)
        trigger_actions = [
            (self.expandBranchAction, self.expandBranch),
            (self.collapseBranchAction, self.collapseBranch),
            (self.collapseAllAction, self.collapseAll),
            (self.hideBranchAction, self.hideBranch),
            (self.showAllAction, self.showAll),
            (self.resetViewAction, self.resetView),
            (self.focusViewAction, self.focusView),
            (self.timeStatsAllAction, self.timeStatsAll),
            (self.timeStatsAction, self.timeStatsSelection),
            (self.snapshotAction, self.createSnapshot),
            (self.visDiffAction, self.visDiffSelection),
            (self.copyOperationAction, self.copyOperation),
            (self.copySequenceAction, self.copySequence),
            (self.pasteOperationAction, self.pasteOperation),
            ]
        for (emitter, receiver) in trigger_actions:
            self.connect(emitter, QtCore.SIGNAL('triggered()'), receiver)

        self.connect(self.keepViewAction,
                     QtCore.SIGNAL('toggled(bool)'),
                     self.keepViewChanged)

    def createMenu(self):
        """ create Menu() -> None
        Create a Plug-in specific menu

        """
        self.fileMenu = self.menuBar().addMenu('&File')
        self.fileMenu.addAction(self.newVistrailAction)
        self.fileMenu.addAction(self.openFileAction)
        self.fileMenu.addAction(self.saveFileAction)
        self.fileMenu.addAction(self.saveFileAsAction)
        self.fileMenu.addAction(self.quitVistrailsAction)

        self.editMenu = self.menuBar().addMenu('&Edit')
        self.editMenu.addAction(self.undoAction)
        self.editMenu.addAction(self.redoAction)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.copyOperationAction)
        self.editMenu.addAction(self.copySequenceAction)
        self.editMenu.addAction(self.pasteOperationAction)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.editPreferencesAction)

        self.viewMenu = self.menuBar().addMenu('&View')
        self.viewMenu.addAction(self.expandBranchAction)
        self.viewMenu.addAction(self.collapseBranchAction)
        self.viewMenu.addAction(self.collapseAllAction)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.hideBranchAction)
        self.viewMenu.addAction(self.showAllAction)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.resetViewAction)
        self.viewMenu.addAction(self.focusViewAction)

        self.toolsMenu = self.menuBar().addMenu('Tools')
        self.toolsMenu.addAction(self.timeStatsAllAction)
        self.toolsMenu.addAction(self.timeStatsAction)
        self.toolsMenu.addAction(self.visDiffAction)
        self.toolsMenu.addSeparator()
        self.toolsMenu.addAction(self.snapshotAction)
        self.toolsMenu.addSeparator()
        self.helpMenu = self.menuBar().addMenu('Help')
        self.helpMenu.addAction(self.helpAction)

        # Add this dummy menu to play nice with the core VisTrails code
        self.vistrailMenu = QtGui.QMenu()

    def updateAddonToolBar(self, vistrailView):
        """ Update the controller for those add-on toolbars """
        if vistrailView:
            controller = vistrailView.controller
        else:
            controller = None
        self.searchToolBar.setController(controller)
        self.playbackToolBar.setController(controller)

    def saveWindowPreferences(self):
        """ Save the current window settings """
        CaptureAPI.setPreference('VisTrailsBuilderWindowGeometry',
                                 self.saveGeometry().toBase64().data())

    def moveEvent(self, event):
        """ Save current window settings right away"""
        self.saveWindowPreferences()
        return QBuilderWindow.moveEvent(self, event)

    def resizeEvent(self, event):
        """ Save current window settings right away"""
        self.saveWindowPreferences()
        return QBuilderWindow.resizeEvent(self, event)

    def quitVistrails(self):
        """ quitVistrails() -> bool
        Quit Vistrail, return False if not succeeded

        """
        if self.viewManager.closeAllVistrails():
            CaptureAPI.unloadPlugin()

        # clean up the temporary directory
        if not self.dbDefault:
            core.system.clean_temporary_save_directory()

        return False

    def expandBranch(self):
        """ expandBranch() -> None
        Expand branch of tree

        """
        controller = self.viewManager.currentWidget().controller
        controller.expand_or_collapse_all_versions_below(controller.current_version, True)

    def collapseBranch(self):
        """ collapseBranch() -> None
        Collapse branch of tree

        """
        controller = self.viewManager.currentWidget().controller
        controller.expand_or_collapse_all_versions_below(controller.current_version, False)

    def collapseAll(self):
        """ collapseAll() -> None
        Collapse all branches of tree

        """
        controller = self.viewManager.currentWidget().controller
        controller.ensure_version_in_view(0)
        controller.collapse_all_versions()

    def hideBranch(self):
        """ hideBranch() -> None
        Hide node and all children

        """
        controller = self.viewManager.currentWidget().controller
        controller.hide_versions_below(controller.current_version)

    def showAll(self):
        """ showAll() -> None
        Show all hidden nodes

        """
        controller = self.viewManager.currentWidget().controller
        controller.show_all_versions()

    def resetView(self):
        """ resetView() -> None
        Reset view to default

        """
        self.viewManager.fitToView(True)

    def focusView(self):
        """ focusView() ->  None
        Reset View to center on selected
        
        """
        controller = self.viewManager.currentWidget().controller
        controller.focus_current_version_in_view()

    def timeStatsAll(self):
        """ timeStatsAll() -> None
        Compute time for all actions

        """
        self.hidePlayback()
        from plugin.pgui.histogram_window import QTimeStatisticsWindow
        if self.timeStatsWindow==None:
            self.timeStatsWindow=QTimeStatisticsWindow(self)
        self.timeStatsWindow.compute(-1,-1)
        self.timeStatsWindow.exec_()

    def timeStatsSelection(self):
        """ timeStatsSelection() -> None
        Select 2 versions and compute the time between them
        
        """
        self.hidePlayback()
        versionView = self.getVersionView()
        if versionView!=None:
            versionView.multiSelectionStart(2, 'Time Statistics',
                                            ('Select the start version',
                                            'Select the end version'))
            self.connect(versionView,
                         QtCore.SIGNAL('doneMultiSelection'),
                         self.timeStatsMultiSelection)
    
    def timeStatsMultiSelection(self, successful, versions):
        """ timeStatsMultiSelection(succesful: bool, version: (int,int) -> None
        multi selecting time stats

        """
        versionView = self.getVersionView()
        if versionView!=None:
            self.disconnect(versionView, QtCore.SIGNAL('doneMultiSelection'),
                            self.timeStatsMultiSelection)
        if successful:
            self.timeStats(versions)

    def timeStats(self, versions):
        """ timeStats(versions: [int, int]) -> None
        Show a time histogram

        """
        if versions[0] < versions[1]:
            start = versions[0]
            end = versions[1]
        else:
            start = versions[1]
            end = versions[0]
        controller = self.viewManager.currentWidget().controller
        if not controller.is_parent(start, end):
            self.showStatusWarning('Selection failed', 'Versions not part of the same branch')
            self.hideTimeStats()
            return
        def finishTimeStats():
            from plugin.pgui.histogram_window import QTimeStatisticsWindow
            if self.timeStatsWindow==None:
                self.timeStatsWindow=QTimeStatisticsWindow(self)
            self.timeStatsWindow.compute(start,end)
            self.connect(self.timeStatsWindow,
                         QtCore.SIGNAL('closed'),
                         self.hideTimeStats)
            self.timeStatsWindow.exec_()
        CaptureAPI.executeDeferred(finishTimeStats)
            
    def hideTimeStats(self):
        """ hideTimeStats() -> None

        """
        self.getVersionView().multiSelectionAbort('Time Statistics')

    def getVersionView(self):
        """ getVersionView() -> QTreeVersionVew
        Return the current version view

        """
        currentView = self.viewManager.currentWidget()
        if currentView:
            return currentView.versionTab.versionView
        return None

    def createSnapshot(self):
        """ createSnapshot() -> None
        Store the contents of the scene in an new version
        
        """
        controller = self.viewManager.currentWidget().controller
        if controller.current_version > 0:
            CaptureAPI.createSnapshot()

    def visDiffSelection(self):
        """ visDiffSelection() -> None
        Select 2 versions and show the visual diff

        """
        self.hidePlayback()
        versionView = self.getVersionView()
        if versionView!=None:
            versionView.multiSelectionStart(2, 'Visual Difference',
                                            ('Select the start version',
                                            'Select the end version'))
            self.connect(versionView,
                         QtCore.SIGNAL('doneMultiSelection'),
                         self.diffMultiSelection)

    def diffMultiSelection(self, successful, versions):
        """ diffMultiSelection(successful: bool) -> None
        Handled the selection is done. successful specifies if the
        selection was completed or aborted by users.

        """
        versionView = self.getVersionView()
        if versionView!=None:
            self.disconnect(versionView, QtCore.SIGNAL('doneMultiSelection'),
                            self.diffMultiSelection)
        if successful:
            self.showVisualDiff(versions)

    def showAboutMessage(self):
        """showAboutMessage() -> None
        Displays Application about message

        """
        QtGui.QMessageBox.about(self, 'About Provenance Explorer', CaptureAPI.getAboutString())

    def keepViewChanged(self, checked=True):
        """ Update app settings accordingly """
        if checked:
            self.keepViewAction.setIcon(CurrentTheme.VIEW_ON_ICON)
            CaptureAPI.setPreference('VisTrailsUseRecordedViews', '0')
        else:
            self.keepViewAction.setIcon(CurrentTheme.VIEW_OFF_ICON)
            CaptureAPI.setPreference('VisTrailsUseRecordedViews', '1')

    def showPreferences(self):
        """showPreferences() -> None
        Display Preferences dialog

        """
        dialog = QPluginPreferencesDialog(self)
        dialog.exec_()

    def copyOperation(self):
        """ copyOperation() -> None
        """
        self.hidePlayback()
        controller = self.viewManager.currentWidget().controller
        current_version = controller.current_version
        # Start at parent of selected version so that we get the action betwen them
        parent_version = controller.get_parent(current_version)
        if parent_version>=0:
            PluginPatch.copy(controller, parent_version, current_version)
            self.statusBar().showMessage('Copied version to clipboard', CurrentTheme.STATUS_TIMER_LENGTH)
            self.pasteOperationAction.setEnabled(True)
        else:
            self.showStatusWarning('Copy failed', 'Invalid version')
            PluginPatch.reset()
            self.pasteOperationAction.setEnabled(False)

    def copySequence(self):
        """ copySequence() -> None

        Select 2 versions and start patching process
        """
        self.hidePlayback()
        versionView = self.getVersionView()
        if versionView!=None:
            versionView.multiSelectionStart(2, 'Copy Sequence',
                                            ('Select the start version',
                                             'Select the end version'))
            self.connect(versionView,
                         QtCore.SIGNAL('doneMultiSelection'),
                         self.copySequenceComplete)

    def copySequenceComplete(self, successful, versions):
        """ copySequenceComplete(successful: bool, versions = [int,int]) -> None

        Handled the selection is done. successful specifies if the
        selection was completed or aborted by users.
        """
        versionView = self.getVersionView()
        if versionView!=None:
            self.disconnect(versionView, QtCore.SIGNAL('doneMultiSelection'),
                            self.copySequenceComplete)
        if successful:
            controller = self.viewManager.currentWidget().controller
            if not PluginPatch.isValidSequence(controller, versions[0], versions[1]):
                self.showStatusWarning('Copy failed', 'Start version not a parent of end version')
                PluginPatch.reset()
                self.pasteOperationAction.setEnabled(False)
            else:
                # Start at the parent of selected version because it is more
                # Intuitive for the user.
                start = versions[0]
                end = versions[1]
                parent = controller.get_parent(start)
                if parent >= 0:
                    start = parent
                PluginPatch.copy(controller, start, end)
                self.pasteOperationAction.setEnabled(True)
                self.statusBar().showMessage('Sequence copied to clipboard', CurrentTheme.STATUS_TIMER_LENGTH)
        QtCore.QTimer.singleShot(CurrentTheme.STATUS_TIMER_LENGTH, self.hideCopy)


    def hideCopy(self):
        """ hideCopy(accepted: bool) -> None

        """
        versionView = self.getVersionView()
        versionView.multiSelectionAbort('Copy Sequence')

    def pasteOperation(self):
        self.hidePlayback()
        def finishPaste():
            PluginPatch.paste()
            self.messageDialog = QMessageDialog('Accept', 'Discard',
                                                'Applied ' + PluginPatch.getReportText() +
                                                ' operation(s).\nAccept the paste?', self)
            self.connect(self.messageDialog,
                         QtCore.SIGNAL('accepted'),
                         self.hidePaste)
            self.messageDialog.show()
            MessageDialogContainer.instance().registerDialog(self.messageDialog)
        CaptureAPI.executeDeferred(finishPaste)

    def hidePaste(self, accepted):
        """
        """
        PluginPatch.finish(accepted)
        if self.messageDialog:
            self.messageDialog.reject()
            MessageDialogContainer.instance().unregisterDialog(self.messageDialog)

    def showVisualDiff(self, versions):
        """ Show the visual diff window """
        startVersion=versions[0]
        endVersion=versions[1]
        controller=self.viewManager.currentWidget().controller
        commonVersion=controller.vistrail.getFirstCommonVersion(startVersion,endVersion)
        CaptureAPI.startVisualDiff(commonVersion,startVersion,endVersion)
        def finishVisualDiff():
            self.messageDialog = QMessageDialog('Close', None,
                                                'Close the Visual Difference?',
                                                self)
            self.connect(self.messageDialog,
                         QtCore.SIGNAL('accepted'),
                         self.hideVisualDiff)
            self.messageDialog.show()
            MessageDialogContainer.instance().registerDialog(self.messageDialog)
            #self.hideVisualDiff(self.messageDialog.execute()=='accepted')
        CaptureAPI.executeDeferred(finishVisualDiff)

    def hideVisualDiff(self,accepted=True):
        """ hideVisualDiff(accepted: bool) -> None
        Clean up the visual diff interface.
        """
        self.getVersionView().multiSelectionAbort('Visual Difference')
        CaptureAPI.stopVisualDiff()

        self.messageDialog.reject()
        MessageDialogContainer.instance().unregisterDialog(self.messageDialog)

        controller = self.viewManager.currentWidget().controller
        controller.update_app_with_current_version(0, False)

    def startProgress(self, text):
        """ startProgress() -> None
        Show the progress bar

        """
        if not self.descriptionWidget.isHidden():
            return
        self.progressLabel.setText(text)
        self.progressLabel.show()
        self.progressWidget.reset()
        self.progressWidget.show()
        # Don't let the user change the version
        self.playbackToolBar.frameSlider.setEnabled(False)
        self.undoAction.setEnabled(False)
        self.redoAction.setEnabled(False)
        if self.getVersionView():
            self.getVersionView().setEnabled(False)
        # Mac needs to process events here or we don't get a redraw
        if core.system.systemType in ['Darwin']:
            QtCore.QCoreApplication.processEvents()

    def endProgress(self):
        """ endProgress() -> None
        Hide the progress bar

        """
        self.progressWidget.hide()
        self.progressLabel.hide()
        # Allow the user to change the version again
        self.playbackToolBar.frameSlider.setEnabled(True)
        currentView = self.viewManager.currentWidget()
        if currentView:
            self.undoAction.setEnabled(currentView.controller.current_version>0)
            self.redoAction.setEnabled(currentView.can_redo())
        if self.getVersionView():
            self.getVersionView().setEnabled(True)
            self.getVersionView().setFocus()

    def updateProgress(self, val):
        """ updateProgress(val: float) -> None
        Set the progress bar status.  val is in (0,1].

        """
        self.progressWidget.setValue(val*100)
        # Mac needs to process events here or we don't get a redraw
        if core.system.systemType in ['Darwin']:
            QtCore.QCoreApplication.processEvents()

    def versionSelectionChange(self, versionId):
        """ versionSelectionChange(versionId: int) -> None
        Setup state of actions
        
        """
        self.undoAction.setEnabled(versionId>0)
        currentView = self.viewManager.currentWidget()
        if currentView:
            self.redoAction.setEnabled(currentView.can_redo())
        else:
            self.redoAction.setEnabled(False)
        if not CaptureAPI.isReadOnly():
            self.snapshotAction.setEnabled(versionId>0)
        
        
    def currentVistrailChanged(self, vistrailView):
        """ currentVistrailChanged(vistrailView: QVistrailView) -> None
        Redisplay the new title of vistrail

        """
        self.execStateChange()
        if vistrailView:
            self.setWindowTitle(self.title + ' - ' +
                                vistrailView.windowTitle())
            if not CaptureAPI.isReadOnly():
                self.saveFileAction.setEnabled(True)
                self.saveFileAsAction.setEnabled(True)
        else:
            self.setWindowTitle(self.title)
            self.saveFileAction.setEnabled(False)
            self.saveFileAsAction.setEnabled(False)

        if vistrailView and vistrailView.viewAction:
            vistrailView.viewAction.setText(vistrailView.windowTitle())
            if not vistrailView.viewAction.isChecked():
                vistrailView.viewAction.setChecked(True)
   
    def vistrailChanged(self):
        """ vistrailChanged() -> None
        An action was performed on the current vistrail

        """
        if not CaptureAPI.isReadOnly():
            self.saveFileAction.setEnabled(True)
            self.saveFileAsAction.setEnabled(True)

    def open_vistrail_without_prompt(self, locator, version=None,
                                     execute_workflow=False):
        """open_vistrail_without_prompt(locator_class, version: int or str,
                                        execute_workflow: bool) -> None
        Open vistrail depending on the locator class given.
        If a version is given, the workflow is shown on the Pipeline View.
        I execute_workflow is True the workflow will be executed.
        """
        if not locator.is_valid():
                ok = locator.update_from_gui()
        else:
            ok = True
        if ok:
            # TODO: Passing in False here breaks the without_prompt intention
            # of the code, but do we even need the distinction in the plug-in?
            view = self.viewManager.open_vistrail(locator, version, False)
            if view == None:
                return
            if CaptureAPI.isReadOnly():
                self.addonToolBar.setEnabled(True)
                self.interactionToolBar.setEnabled(True)
                self.editMenu.setEnabled(True)
                self.toolsMenu.setEnabled(True)
                self.viewMenu.setEnabled(True)
            else:
                self.saveFileAsAction.setEnabled(True)
            if version:
                self.emit(QtCore.SIGNAL("changeViewState(int)"), 0)
                self.viewModeChanged(0)
            else:
                self.emit(QtCore.SIGNAL("changeViewState(int)"), 1)
                self.viewModeChanged(1)
            if execute_workflow:
                self.execute_current_pipeline()
                
    def hidePlayback(self):
        if self.playbackToolBar.isVisible():
            self.playbackToolBar.hide()

    def showStatusWarning(self, errorText, messageText):
        """ showStatusWarning(errorText: str, messageText: str) -> None 
        
        Status bar messages cannot be changed to rich text so we need to add
        our own label into the status bar for red warning messages
        """
        self.statusWarning = QtGui.QLabel('<html><span style="color:#D80000"><b>'+errorText+': </b>'+messageText+'</html>', self)
        self.statusBar().addWidget(self.statusWarning)
        QtCore.QTimer.singleShot(CurrentTheme.STATUS_TIMER_LENGTH, self.hideStatusWarning)

    def hideStatusWarning(self):
        """ hideStatusWarning() -> None

        """
        if self.statusWarning != None:
            self.statusBar().removeWidget(self.statusWarning)
            self.statusWarning = None
