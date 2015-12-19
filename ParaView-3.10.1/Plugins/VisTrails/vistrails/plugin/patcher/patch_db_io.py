
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
import array
import core.requirements
import db.services.io
import os
import os.path
import tempfile
import time
import zipfile
import shutil
from gui.version_view import QVersionTreeView
from gui.utils import getBuilderWindow
from core.system import execute_cmdline
from db.versions import getVersionDAO, currentVersion
from db.services.io import save_vistrail_to_xml, open_vistrail_from_xml,\
    unzip_file


tempDir = []
    
    
def addFolderToZipFile(zf, basedir, _type):
    assert os.path.isdir(basedir)
    
    try:
        for root, dirs, files in os.walk(basedir):
            for fn in files:
                fname = os.path.join(root, fn)
                if os.name == "posix":
                    if _type == "audio":
                        destName = "audio//%s" % os.path.basename(fname)
                    elif _type == "video":
                        destName = "video//%s" % os.path.basename(fname)
                elif os.name == "nt":
                    if _type == "audio":
                        destName = "audio\\%s" % os.path.basename(fname)
                    elif _type == "video":
                        destName = "video\\%s" % os.path.basename(fname)

                zf.write(fname, destName, zipfile.ZIP_DEFLATED)

    except Exception:
        raise Exception('Unable to save files')


def new_save_vistrail_to_zip_xml(vistrail, filename):
    # Dumb hack to figure out if we are autosaving 
    if filename.find('vt_autosaves') > 0:
        getBuilderWindow().startProgress('Autosaving...')
    else:
        getBuilderWindow().startProgress('Saving...')

    # Write the vistrail file to disk
    (file_, xmlfname) = tempfile.mkstemp(suffix='.xml')
    os.close(file_)
    save_vistrail_to_xml(vistrail,xmlfname)
    vt_fname = os.path.join(os.path.dirname(xmlfname), 'vistrail')
    if os.path.exists(vt_fname):
        os.remove(vt_fname)
    os.rename(xmlfname, vt_fname)
    zip_fnames = [vt_fname, ]

    #Audio Dir
    ###################################################
    zip_audio_folder = []
    audio_dir = vistrail.db_audio_dir
    zip_audio_folder.append(audio_dir)
    ###################################################
    #Video Dir
    ###################################################
    zip_video_folder = []
    video_dir = vistrail.db_video_dir
    zip_video_folder.append(video_dir)
    ###################################################

    getBuilderWindow().updateProgress(0.2)

    # Save binary data
    (bin_file, bin_filename) = tempfile.mkstemp(suffix='.bin')
    os.close(bin_file)
    bfile = open(bin_filename, "wb")
    vistrail.binary_data.tofile(bfile)
    bfile.close()
    bin_fname = os.path.join(os.path.dirname(bin_filename), 'data')
    if os.path.exists(bin_fname):
        os.remove(bin_fname)
    os.rename(bin_filename, bin_fname)
    zip_fnames.append(bin_fname)
    
    getBuilderWindow().updateProgress(0.5)

    if vistrail.log is not None and len(vistrail.log.workflow_execs) > 0:
        if vistrail.log_filename is None:
            (log_file, log_filename) = tempfile.mkstemp(suffix='.xml')
            os.close(log_file)
            log_file = open(log_filename, "wb")
        else:
            log_filename = vistrail.log_filename
            log_file = open(log_filename, 'ab')

        print "+++ ", log_filename
        print "*** ", log_file
        if not hasattr(log_file, "write"):
            print "no!!!"
        
        # append log to log_file
        for workflow_exec in vistrail.log.workflow_execs:
            daoList = getVersionDAO(currentVersion)
            daoList.save_to_xml(workflow_exec, log_file, {}, currentVersion)
        log_file.close()

        log_fname = os.path.join(os.path.dirname(log_filename), 'log')
        if os.path.exists(log_fname):
            os.remove(log_fname)
        os.rename(log_filename, log_fname)
        zip_fnames.append(log_fname)

    try:
        zf = zipfile.ZipFile(file=filename,mode='w',
                             allowZip64=True)
        # Add standard vistrails files
        for f in zip_fnames:
            zf.write(f,os.path.basename(f),zipfile.ZIP_DEFLATED)

        if zip_audio_folder[0] != None:
            if os.path.isdir(zip_audio_folder[0]) == True:
                for d in zip_audio_folder:
                    addFolderToZipFile(zf, d, "audio")
        
        if zip_video_folder[0] != None:
            if os.path.isdir(zip_video_folder[0]) == True:
                for v in zip_video_folder:
                    addFolderToZipFile(zf, v, "video")
                    

        getBuilderWindow().updateProgress(0.75)
        # Add saved files. Append indicator of file type because it needed
        # when extracting the zip on Windows
        for (f,b) in vistrail.saved_files:
            basename = os.path.join("vt_saves",os.path.basename(f))
            if b:
                basename += ".b"        
            else:
                basename += ".a"
            zf.write(f, basename, zipfile.ZIP_DEFLATED)
        zf.close()
        
        currentFolder = []
        
    except Exception, e:
        # Allow autosaves to fail silently
        if filename.find('vt_autosaves') <0:
            raise Exception('Error writing file!\nThe file may be invalid or you\nmay have insufficient permissions.')


    getBuilderWindow().updateProgress(0.95)
        
    # Remove temporary files
    for f in zip_fnames:
        os.unlink(f)

    getBuilderWindow().endProgress()

    return vistrail

def new_open_vistrail_from_zip_xml(filename):
    """open_vistrail_from_zip_xml(filename) -> Vistrail
    Open a vistrail from a zip compressed format.
    It expects that the file inside archive has name vistrail

    """
    
    try:
        zf = zipfile.ZipFile(filename, 'r')
    except:
        raise Exception('Error opening file!\nThe file may be invalid or you\nmay have insufficient permissions.')
    
    getBuilderWindow().startProgress('Opening...')

    #######################################################
    #Audio and Video
    sourceZip = zipfile.ZipFile(filename)
    
    tmp_audio_dir = tempfile.mkdtemp(prefix="VTAudio")
    audio_dir = os.path.join(tmp_audio_dir)
    os.mkdir(os.path.join(tmp_audio_dir, "audio"))
    
    tmp_video_dir = tempfile.mkdtemp(prefix="VTVideo")
    video_dir = os.path.join(tmp_video_dir)
    os.mkdir(os.path.join(tmp_video_dir, "video"))
    
    # Unzip vistrail
    (file_, xmlfname) = tempfile.mkstemp(suffix='.xml')
    os.close(file_)
    file(xmlfname, 'w').write(zf.read('vistrail'))
    vistrail = open_vistrail_from_xml(xmlfname)
    vistrail.db_audio_dir = os.path.join(tmp_audio_dir)
    vistrail.db_video_dir = os.path.join(tmp_video_dir)
    os.unlink(xmlfname)

    getBuilderWindow().updateProgress(0.3)
    
    # Unzip data file
    (bfile_, binfname) = tempfile.mkstemp()
    os.close(bfile_)
    file(binfname, 'wb').write(zf.read('data'))
    vistrail.binary_data = array.array('c')
    bsize = os.path.getsize(binfname)
    vt_bin_file = open(binfname, 'rb')
    vistrail.binary_data.fromfile(vt_bin_file, bsize)
    vt_bin_file.close()
    os.unlink(binfname)
    
    getBuilderWindow().updateProgress(0.7)
    
    # Unzip save data
    namelist = zf.namelist()
    vistrail.saved_files = []
    for name in namelist:
        if name != "vistrail" and name != "data" and \
                not name.startswith("audio" + os.sep) and not name.startswith("video" + os.sep) and not name.startswith("audio") and not name.startswith("video"):
            # Filename has a '.b' or '.a' appended to it so we know
            # how to write it.  In Python 2.6 or later, we should just use
            # zipFile.extractAll instead of zipFile.read
            (basename,ext) = os.path.splitext(name)
            sfilename = core.system.temporary_save_file(os.path.basename(basename))
            print "sfilename, ", sfilename
            print "name, ", name
            if ext == ".b":
                file(sfilename, 'wb').write(zf.read(name))
            else:
                file(sfilename, 'w').write(zf.read(name))
            vistrail.saved_files.append((sfilename, ext))

    getBuilderWindow().endProgress()

    temp_audio_Dir = vistrail.db_audio_dir
    temp_video_Dir = vistrail.db_video_dir
    
    return vistrail



def new_open_vistrail_from_zip_xml_old(filename):
    """open_vistrail_from_zip_xml(filename) -> Vistrail
    Open a vistrail from a zip compressed format.
    It expects that the file inside archive has name vistrail

    """
    try:
        zf = zipfile.ZipFile(filename, 'r')
    except:
        raise Exception('Error opening file!\nThe file may be invalid or you\nmay have insufficient permissions.')
    
    getBuilderWindow().startProgress('Opening...')
    

    #######################################################
    #Audio and Video
    sourceZip = zipfile.ZipFile(filename)
    tmp_audio_dir = tempfile.mkdtemp(prefix="VTAudio")
    audio_dir = os.path.join(tmp_audio_dir)
    tmp_video_dir = tempfile.mkdtemp(prefix="VTVideo")
    video_dir = os.path.join(tmp_video_dir)
    

    for name in sourceZip.namelist():
        if name.find('.mp3') != -1 or name.find('.wav') != -1 or name.find('.ogg') != -1 or \
name.find('.mpc') != -1 or name.find('.flac') != -1 or name.find('.au') != -1 or \
name.find('.raw') != -1 or name.find('.dct') != -1 or name.find('.aac') != -1 or \
name.find('.m4a') != -1 or name.find('.wma') != -1 or \
name.find('.amr') != -1 or name.find('.awb'):
            if name.startswith('audio/VTAudio') == True:
                sourceZip.extract(name, tmp_audio_dir)
            
        if name.find('.3g2') != -1 or name.find('.3gp') != -1 or name.find('.amv') != -1 or \
name.find('.asf') != -1 or name.find('.asx') != -1 or name.find('.avi') != -1 or \
name.find('.wmv') != -1 or name.find('.vob') != -1 or name.find('.wwf') != -1 or \
name.find('.rm') != -1 or name.find('.mpg') != -1 or name.find('.mov') != -1 or \
name.find('.flv') != -1 or name.find('.mp4'):
            if name.startswith('video/VTVideo') == True:
                sourceZip.extract(name, tmp_video_dir)
    
    
    # Unzip vistrail
    (file_, xmlfname) = tempfile.mkstemp(suffix='.xml')
    os.close(file_)
    file(xmlfname, 'w').write(zf.read('vistrail'))
    vistrail = open_vistrail_from_xml(xmlfname)
    vistrail.db_audio_dir = os.path.join(tmp_audio_dir)
    vistrail.db_video_dir = os.path.join(tmp_video_dir)
    os.unlink(xmlfname)

    getBuilderWindow().updateProgress(0.3)
    
    # Unzip data file
    (bfile_, binfname) = tempfile.mkstemp()
    os.close(bfile_)
    file(binfname, 'wb').write(zf.read('data'))
    vistrail.binary_data = array.array('c')
    bsize = os.path.getsize(binfname)
    vt_bin_file = open(binfname, 'rb')
    vistrail.binary_data.fromfile(vt_bin_file, bsize)
    vt_bin_file.close()
    os.unlink(binfname)

    getBuilderWindow().updateProgress(0.7)

    # Unzip save data
    namelist = zf.namelist()
    vistrail.saved_files = []
    for name in namelist:
        if name != "vistrail" and name != "data" and \
                not name.startswith("audio" + os.sep) and not name.startswith("video" + os.sep) and not name.startswith("audio") and not name.startswith("video"):
            # Filename has a '.b' or '.a' appended to it so we know
            # how to write it.  In Python 2.6 or later, we should just use
            # zipFile.extractAll instead of zipFile.read
            (basename,ext) = os.path.splitext(name)
            sfilename = core.system.temporary_save_file(os.path.basename(basename))
            print "sfilename, ", sfilename
            print "name, ", name
            if ext == ".b":
                file(sfilename, 'wb').write(zf.read(name))
            else:
                file(sfilename, 'w').write(zf.read(name))
            vistrail.saved_files.append((sfilename, ext))

    getBuilderWindow().endProgress()

    temp_audio_Dir = vistrail.db_audio_dir
    temp_video_Dir = vistrail.db_video_dir
    
    return vistrail


db.services.io.save_vistrail_to_zip_xml = new_save_vistrail_to_zip_xml
db.services.io.open_vistrail_from_zip_xml = new_open_vistrail_from_zip_xml
