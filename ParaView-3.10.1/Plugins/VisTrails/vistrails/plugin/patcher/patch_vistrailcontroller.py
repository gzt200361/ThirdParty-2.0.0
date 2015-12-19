
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
# Patch VistrailController
from PyQt4 import QtCore, QtGui
from PyQt4.phonon import Phonon
from core.log.log import Log
from core.vistrail.action import Action
from core.vistrail.operation import AddOp
from core.vistrail.plugin_data import PluginData
from core.vistrail.pipeline import Pipeline
from core.vistrails_tree_layout_lw import VistrailsTreeLayoutLW
from db.domain import DBWorkflow
from db.services.vistrail import performActions
import core.db.action
import cPickle
import CaptureAPI
import sys

def VC___init__(self, vis=None, auto_save=True, name=''):
    """ VistrailController(vis: Vistrail, name: str) -> VistrailController
    Create a controller from vis

    """
    QtCore.QObject.__init__(self)
    self.name = ''
    self.file_name = ''
    self.set_file_name(name)
    self.vistrail = vis
    self.log = Log()
    self.current_version = -1
    self.current_pipeline = None
    self.audio_dir = None
    self.video_dir = None
    self.audioMediaObject = None
    self.videoMediaObject = None
    self.current_pipeline_view = None
    self.vistrail_view = None
    self.reset_pipeline_view = False
    self.reset_version_view = True
    self.quiet = False
    self.search = None
    self.search_str = None
    self.refine = False
    self.changed = False
    self.full_tree = False
    self.analogy = {}
    self._auto_save = auto_save
    self.locator = None
    self.timer = QtCore.QTimer(self)
    self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.write_temporary)
    self.reset_autosave_timer()
    self.need_view_adjust = True
    self.playback_start = -1
    self.playback_end = -1
    self._current_graph_layout = VistrailsTreeLayoutLW()
    self.animate_layout = False
    self.presetOps = ''
    self.num_versions_always_shown = int(CaptureAPI.getPreference('VisTrailsNumberOfVisibleVersions'))
    self.snapshot_action_count = 0
    self.num_versions_when_autosaved = 0

def VC_reset_autosave_timer(self):
    """ reset_autosave_timer() -> None

    Change Autosave parameters
    """
    
    if int(CaptureAPI.getPreference('VisTrailsAutosaveEnabled')) and not CaptureAPI.isReadOnly():
        self.timer.stop()
        self.timer.start(1000 * 60 * int(CaptureAPI.getPreference('VisTrailsAutosaveDelay')))
    else:
        self.timer.stop()

def VC_change_selected_version(self, newVersion):
    if self.current_version==newVersion: return
    old_version = self.current_version
    self.current_version = newVersion
    if newVersion>=0:
        try:
            self.current_pipeline = self.vistrail.getPipeline(newVersion)
            self.current_pipeline.ensure_connection_specs()
        except: 
            from gui.application import VistrailsApplication
            QtGui.QMessageBox.critical(VistrailsApplication.builderWindow,
                                       'Versioning Error',
                                       ('Cannot open selected version because of unsupported operations'))
            self.current_pipeline = None
            self.current_version = 0
    else:
        self.current_pipeline = None
    # Bail out for now
    self.recompute_terse_graph()
    self.invalidate_version_tree(False)
    self.ensure_version_in_view(newVersion)
    self.emit(QtCore.SIGNAL('versionWasChanged'), newVersion)
    #### Host Application BEGIN
    self.update_app_with_current_version(old_version)
    #### Host Application END

def idx2str(indices):
    return str(indices[0]) + ':' + str(indices[1])

def str2idx(s):
    return map(int, s.split(':'))

def VC_update_scene_script(self, description, details, snapshot, script):
    """ update_scene_script(description: string, details: string, snapshot: int, script: string) -> None

    """
    if self.current_pipeline:
        indices = self.vistrail.store_string(script)
        p = PluginData(id=self.vistrail.idScope.getNewId(PluginData.vtType),
                       data = idx2str(indices))
        add_op = AddOp(id=self.vistrail.idScope.getNewId(AddOp.vtType),
                       what=PluginData.vtType,
                       objectId=p.id,
                       data=p)
        action = Action(id=self.vistrail.idScope.getNewId(Action.vtType),
                        operations=[add_op])

        self.add_new_action(action)
        if len(description) > 25:
            description = description[0:22] + "..."
            
        if CaptureAPI.isReadOnly():
            self.vistrail.hideVersion(self.current_version)
        self.vistrail.change_description(description, self.current_version)
        self.vistrail.change_details(details, self.current_version)
        self.vistrail.change_snapshot(snapshot, self.current_version)
        self.perform_action(action)
        self.reset_pipeline_view = True
        self.emit(QtCore.SIGNAL('versionWasChanged'), self.current_version)
        self.reset_pipeline_view = False
        self.recompute_terse_graph()
        self.invalidate_version_tree(False)
        self.ensure_version_in_view(self.current_version)
        self.emit(QtCore.SIGNAL('scene_updated'))
        if not snapshot and not CaptureAPI.isReadOnly():
            self.snapshot_action_count += 1
            if CaptureAPI.getPreference('VisTrailsSnapshotEnabled') is not None and \
               int(CaptureAPI.getPreference('VisTrailsSnapshotEnabled')) and \
                    self.snapshot_action_count >= int(CaptureAPI.getPreference('VisTrailsSnapshotCount')):
                self.snapshot_action_count = 0
                CaptureAPI.createSnapshot()
        else:
            self.snapshot_action_count = 0

def VC_getOpsFromPipeline(self, pipeline):
    ops = ''
    pds = pipeline.plugin_datas
    for pd in pds:
        indices = str2idx(pd.data)
        ops+=self.vistrail.get_string(indices)
    return ops

def getPipeline(actions):
    workflow = DBWorkflow()
    performActions(actions, workflow)
    Pipeline.convert(workflow)
    return workflow

def VC_get_latest_snapshot_index(self):
    """ get_latest_snapshot_index() -> int 
    Traverse the actions in the current pipeline in reverse order and return the
    index of the last snapshot.

    """
    actions = self.vistrail.actionChain(self.current_version)
    length = len(actions)
    for i in xrange(length-1,-1,-1):
        if self.vistrail.get_snapshot(actions[i].id):
            return i
    return 0


def VC_extract_ops(self, commonVersion, oldVersion, newVersion, startVersion=0, brief=True):
    """ Returns the new ops, the old ops, and the shared ops after the given 
    start version (required to be a parent of the common version).
    It is very naive now, there are 3 get pipeline calls. In the
    future we need to convert actions directly into application modules to
    avoid wasting memory. But it is good for now with partial updates
    on application side. """
    pNew = getPipeline(self.vistrail.actionChain(newVersion, commonVersion))
    if brief and commonVersion==oldVersion:
        return ('', '', self.getOpsFromPipeline(pNew))
    pShared = getPipeline(self.vistrail.actionChain(commonVersion,startVersion))
    pOld = getPipeline(self.vistrail.actionChain(oldVersion, commonVersion))
    return (self.getOpsFromPipeline(pShared),
            self.getOpsFromPipeline(pOld),
            self.getOpsFromPipeline(pNew))

def VC_extract_ops_per_version(self, startVersion, endVersion):
    """ Similar to the extract_ops but categorize all of them into a
    series of ops for each version """
    actions = self.vistrail.actionChain(endVersion, startVersion)
    ops = [self.getOpsFromPipeline(getPipeline([action]))
           for action in actions]
    return ops

def VC_diff_ops_linear(self, v1, v2):
    """ Return the list of ops changes from version v1 to version v2 """
    result = {}
    v = v2
    while 1:
        if v==v1:
            result[v] = None
            break
        if v==0: return None
        action = self.vistrail.actionMap[v]
        result[v] = self.getOpsFromPipeline(getPipeline([action]))
        v = action.parent
    return result

def VC_update_app_with_current_version(self, oldVersion = 0, partialUpdates=True):
    if self.current_pipeline:
        from gui.application import VistrailsApplication
        if VistrailsApplication.builderWindow.updateApp:
            currentVersion = self.current_version
            if CaptureAPI.flushCurrentContext(oldVersion):
                oldVersion = self.current_version
                VistrailsApplication.builderWindow.changeVersionWithoutUpdatingApp(currentVersion)
            commonVersion = self.vistrail.getFirstCommonVersion(oldVersion, currentVersion)
            useCamera = int(CaptureAPI.getPreference('VisTrailsUseRecordedViews'))
            CaptureAPI.updateAppWithCurrentVersion(partialUpdates,commonVersion,oldVersion,currentVersion,int(useCamera))

def VC_ensure_version_in_view(self, newVersion):
    """ Ensure the version is visible in the vistrail_view """
    if self.vistrail_view and newVersion>=0:
        versionView = self.vistrail_view.versionTab.versionView
        if newVersion in versionView.scene().versions:
            versionView.ensureVisible(versionView.scene().versions[newVersion], 0, 0)

def VC_focus_current_version_in_view(self):
    """ Ensure the current version is in view """
    if self.vistrail_view and self.current_version>=0:
        versionView = self.vistrail_view.versionTab.versionView
        if self.current_version in versionView.scene().versions:
            versionView.resetTransform()
            versionView.scale(0.5, 0.5)
            versionView.centerOn(versionView.scene().versions[self.current_version])            

def VC_store_preset_attributes(self):    
    """ Inspect the state and store all preset attributes into the
    plugin_info annotation."""
    self.vistrail.plugin_app_info=CaptureAPI.getAppString()
    self.vistrail.plugin_version_info=CaptureAPI.getAppVersionNumber()
    CaptureAPI.storePresetAttributes()

def VC_finish_store_preset_attributes(self,info):    
    """ Inspect the scene and store all preset attributes into the
    plugin_info annotation."""
    indices=self.vistrail.store_string(info)
    self.vistrail.plugin_info=idx2str(indices)
    self.presetOps = info

def VC_load_preset_attributes(self):
    """ Load the preset attributes from the plugin_info annotation """
    if self.vistrail.plugin_info!='':
        indices = str2idx(self.vistrail.plugin_info)
        self.presetOps = self.vistrail.get_string(indices)
    if self.vistrail.plugin_app_info != '' and self.vistrail.plugin_version_info != '':
        if self.vistrail.plugin_app_info != CaptureAPI.getAppString():
            raise Exception("Error Opening File!\nThe vistrail was captured using different software.")            
        elif int(self.vistrail.plugin_version_info) > CaptureAPI.getAppVersionNumber():
            raise Exception("Error Opening File!\nThe vistrail was captured using a newer version of the software.")

def VC_get_preset_attributes(self):
    """ Get the current preset attributes """
    return self.presetOps

def VC_set_vistrail(self, vistrail, locator):
    original_set_vistrail(self, vistrail, locator)
    self.load_preset_attributes()
    self.audio_dir = vistrail.db_audio_dir
    self.video_dir = vistrail.db_video_dir
    

def nukeDir(func, path, exc):
    import os
    import sys
    import errno
    excvalue = exc[1]
    if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
        func(path)
    else:
        raise

def VC_setAudioMediaObject(self, media):
    self.audioMediaObject = media


def VC_setVideoMediaObject(self, media):
    self.videoMediaObject = media


def VC_cleanup(self):
    import shutil
    import os
    
    if self.audioMediaObject == None:
        pass
    else:
        self.audioMediaObject.stop()
        self.audioMediaObject.setCurrentSource(Phonon.MediaSource(QtCore.QUrl.fromLocalFile("")))
        
    if self.videoMediaObject == None:
        pass
    else:
        self.videoMediaObject.videoDir = None
        self.videoMediaObject.stopVideo()
        self.videoMediaObject.exitVideo()
        self.videoMediaObject.resetCurrentSource()
        
            
    locator = self.get_locator()
    if locator:
        locator.clean_temporaries()
    self.vistrail.clean_saved_files()
    self.disconnect(self.timer, QtCore.SIGNAL("timeout()"), self.write_temporary)
    self.timer.stop()
    if self.audio_dir:
        if os.name == 'nt':
            shutil.rmtree(self.audio_dir, ignore_errors=False, onerror=nukeDir)
        else:
            shutil.rmtree(self.audio_dir)
    if self.video_dir:
        if os.name == 'nt':
            shutil.rmtree(self.video_dir, ignore_errors=False, onerror=nukeDir)
        else:
            shutil.rmtree(self.video_dir)

def VC_expand_versions(self, v1, v2):
        """ expand_versions(v1: int, v2: int) -> None
        Expand all versions between v1 and v2
        
        """
        full = self.vistrail.getVersionGraph()
        changed = False
        p = full.parent(v2)
        # Check if all are same
        curr_desc = self.vistrail.get_description(p)
        prev_desc = self.vistrail.get_description(v2)
        expand_all = True
        while p>v1:
            curr_desc = self.vistrail.get_description(p)
            if curr_desc != prev_desc:
                expand_all = False
                break
            p = full.parent(p)
        p = full.parent(v2)
        prev_desc = self.vistrail.get_description(v2)
        while p>v1:
            curr_desc = self.vistrail.get_description(p)
            if expand_all or prev_desc != curr_desc:
                self.vistrail.expandVersion(p)
                changed = True
            p = full.parent(p)
            prev_desc = curr_desc
        if changed:
            self.set_changed(True)
        self.recompute_terse_graph()
        self.invalidate_version_tree(False, True)

def VC_get_parent(self, version):
    if (version > 0):
        full = self.vistrail.getVersionGraph()
        p = full.parent(version)
        return p
    else:
        return -1

def VC_is_immediate_parent(self, parent_version, child_version):
    full = self.vistrail.getVersionGraph()
    p = full.parent(child_version)
    if p == parent_version:
        return 1
    return 0

def VC_is_parent(self, parent_version, child_version):
    full = self.vistrail.getVersionGraph()
    p = full.parent(child_version)
    while p != parent_version and p > 0:
        p = full.parent(p)
    return  p == parent_version


def VC_write_vistrail(self, locator):
    if self.vistrail and (self.changed or self.locator != locator):
        # FIXME hack to use db_currentVersion for convenience
        # it's not an actual field
        self.vistrail.db_currentVersion = self.current_version
        self.vistrail.db_audio_dir = self.audio_dir
        self.vistrail.db_video_dir = self.video_dir

        if self.locator != locator:
            old_locator = self.get_locator()
            self.locator = locator
            new_vistrail = self.locator.save_as(self.vistrail)
            self.set_file_name(locator.name)
            if old_locator:
                old_locator.clean_temporaries()
        else:
            new_vistrail = self.locator.save(self.vistrail)
        if id(self.vistrail) != id(new_vistrail):
            new_version = new_vistrail.db_currentVersion
            self.set_vistrail(new_vistrail, locator)
            self.change_selected_version(new_version)
            self.invalidate_version_tree(False)
        self.set_changed(False)

import gui.vistrail_controller
gui.vistrail_controller.VistrailController.__init__ = VC___init__
gui.vistrail_controller.VistrailController.reset_autosave_timer = VC_reset_autosave_timer
gui.vistrail_controller.VistrailController.change_selected_version = VC_change_selected_version
gui.vistrail_controller.VistrailController.update_scene_script = VC_update_scene_script
gui.vistrail_controller.VistrailController.diff_ops_linear = VC_diff_ops_linear
gui.vistrail_controller.VistrailController.extract_ops_per_version = VC_extract_ops_per_version
gui.vistrail_controller.VistrailController.ensure_version_in_view = VC_ensure_version_in_view
gui.vistrail_controller.VistrailController.focus_current_version_in_view = VC_focus_current_version_in_view
original_set_vistrail = gui.vistrail_controller.VistrailController.set_vistrail
gui.vistrail_controller.VistrailController.set_vistrail = VC_set_vistrail
gui.vistrail_controller.VistrailController.get_latest_snapshot_index = VC_get_latest_snapshot_index

gui.vistrail_controller.VistrailController.update_app_with_current_version = VC_update_app_with_current_version
gui.vistrail_controller.VistrailController.extract_ops = VC_extract_ops
gui.vistrail_controller.VistrailController.store_preset_attributes = VC_store_preset_attributes
gui.vistrail_controller.VistrailController.finish_store_preset_attributes = VC_finish_store_preset_attributes
gui.vistrail_controller.VistrailController.load_preset_attributes = VC_load_preset_attributes
gui.vistrail_controller.VistrailController.get_preset_attributes = VC_get_preset_attributes
gui.vistrail_controller.VistrailController.getOpsFromPipeline = VC_getOpsFromPipeline
gui.vistrail_controller.VistrailController.cleanup = VC_cleanup
gui.vistrail_controller.VistrailController.expand_versions = VC_expand_versions
gui.vistrail_controller.VistrailController.get_parent = VC_get_parent
gui.vistrail_controller.VistrailController.is_immediate_parent = VC_is_immediate_parent
gui.vistrail_controller.VistrailController.is_parent = VC_is_parent
gui.vistrail_controller.VistrailController.write_vistrail = VC_write_vistrail
gui.vistrail_controller.VistrailController.setAudioMediaObject = VC_setAudioMediaObject
gui.vistrail_controller.VistrailController.setVideoMediaObject = VC_setVideoMediaObject

