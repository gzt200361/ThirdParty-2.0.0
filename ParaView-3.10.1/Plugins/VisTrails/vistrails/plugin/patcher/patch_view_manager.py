
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
# Patch QViewManager

from PyQt4 import QtGui, QtCore
from gui.vistrail_view import QVistrailView
import gui.view_manager
from core.db.locator import FileLocator, untitled_locator
from core.vistrail.vistrail import Vistrail
import core.system
from gui.utils import getBuilderWindow

def QVM_new_init(self, parent=None):
    """ QViewManager(parent: QWidget) -> QViewManager
    Create a tab widget without the tabs

    """
    QtGui.QTabWidget.__init__(self, parent)
    self.set_single_document_mode(True)
    self.splittedViews = {}
    self.activeIndex = -1
    self._views = {}

def QVM_fitToView(self, recompute_bounding_rect):
    vistrailView = self.currentWidget()
    if vistrailView:
        versionView = vistrailView.versionTab.versionView
        versionView.scene().fitToView(versionView, recompute_bounding_rect)

def QVM_newVistrail(self, recover_files=True, callBeforeNewVistrail=True):
    """ newVistrail() -> (None or QVistrailView)
    Create a new vistrail with no name. If user cancels process,
    returns None.

    FIXME: We should do the interactive parts separately.
    
    """
    if self.single_document_mode and self.currentView():
        if not self.closeVistrail():
            return None

    # we're actually going to do it
    if callBeforeNewVistrail:
        import CaptureAPI
        CaptureAPI.beforeNewVistrail()

    if recover_files and untitled_locator().has_temporaries():
        import copy
        locator = copy.copy(untitled_locator())
        vistrail = locator.load()
    else:
        locator = None
        vistrail = Vistrail()
    return self.set_vistrail_view(vistrail, locator)


def QVM_save_vistrail(self, locator_class,
                      vistrailView=None,
                      force_choose_locator=False):
    """
    
    force_choose_locator=True triggers 'save as' behavior
    """
    import CaptureAPI
    if CaptureAPI.isReadOnly():
        return False

    if not vistrailView:
        vistrailView = self.currentWidget()
    vistrailView.flush_changes()
    
    if vistrailView:
        gui_get = locator_class.save_from_gui
        # get a locator to write to
        if force_choose_locator:
            locator = gui_get(self, Vistrail.vtType,
                              vistrailView.controller.locator)
        else:
            locator = (vistrailView.controller.locator or
                       gui_get(self, Vistrail.vtType,
                               vistrailView.controller.locator))
        if locator == untitled_locator():
            locator = gui_get(self, Vistrail.vtType,
                                  vistrailView.controller.locator)
        # if couldn't get one, ignore the request
        if not locator:
            return False
        try:
            vistrailView.controller.write_vistrail(locator)
        except Exception, e:
            QtGui.QMessageBox.critical(None,
                                       'Vistrails',
                                       str(e))
            return False
        return True
    return False


def QVM_closeVistrail(self, vistrailView=None, quiet=False):
    """ closeVistrail(vistrailView: QVistrailView, quiet: bool) -> bool
    Close the current active vistrail
    
    """
    import CaptureAPI
    if CaptureAPI.isReadOnly():
        quiet=True
    
    if hasattr(self, "canCancelClose"):
        canCancel = self.canCancelClose
    else:
        canCancel = True
        
    if not vistrailView:
        vistrailView = self.currentWidget()
    vistrailView.flush_changes()
    
    if vistrailView:
        if not quiet and vistrailView.controller.changed:
            text = vistrailView.controller.name
            if text=='':
                text = 'Untitled%s'%core.system.vistrails_default_file_type()
            text = ('Vistrail ' +
                    QtCore.Qt.escape(text) +
                    ' contains unsaved changes.\n Do you want to '
                    'save changes before closing it?')
            
            if canCancel:
                res = QtGui.QMessageBox.information(getBuilderWindow(),
                                                    'Vistrails',
                                                    text, 
                                                    '&Save', 
                                                    '&Discard',
                                                    'Cancel',
                                                    0,
                                                    2)
            else:
                res = QtGui.QMessageBox.information(getBuilderWindow(),
                                                    'Vistrails',
                                                    text, 
                                                    '&Save', 
                                                    '&Discard')
        else:
            res = 1
        if res == 0:
            locator = vistrailView.controller.locator
            if locator is None:
                class_ = FileLocator()
            else:
                class_ = type(locator)
            return self.save_vistrail(class_)
        elif res == 2:
            return False
        self.removeVistrailView(vistrailView)
        if self.count()==0:
            self.emit(QtCore.SIGNAL('currentVistrailChanged'), None)
            self.emit(QtCore.SIGNAL('versionSelectionChange'), -1)
    if vistrailView == self._first_view:
        self._first_view = None
    return True

gui.view_manager.QViewManager.__init__ = QVM_new_init
gui.view_manager.QViewManager.fitToView = QVM_fitToView
gui.view_manager.QViewManager.newVistrail = QVM_newVistrail
gui.view_manager.QViewManager.save_vistrail = QVM_save_vistrail
gui.view_manager.QViewManager.closeVistrail = QVM_closeVistrail
