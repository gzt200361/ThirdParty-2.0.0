
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
## Copyright (C) 2009 VisTrails, Inc. All rights reserved.
##
############################################################################


CMAKE_MINIMUM_REQUIRED(VERSION 2.4)
IF(COMMAND CMAKE_POLICY)
  CMAKE_POLICY(SET CMP0003 NEW)
ENDIF(COMMAND CMAKE_POLICY)

PROJECT(VistrailsPlugin)

if(NOT ParaView_SOURCE_DIR)
  FIND_PACKAGE(ParaView REQUIRED)
  INCLUDE(${PARAVIEW_USE_FILE})
endif()

INCLUDE_DIRECTORIES(
  ${VTK_INCLUDE_DIR}
  ${PARAVIEW_INCLUDE_DIRS}
  ${PARAVIEW_GUI_INCLUDE_DIRS}
  ${PARAVIEW_KWSYS_INCLUDE_DIRS}
  ${pqCore_SOURCE_DIR}
  ${pqCore_BINARY_DIR}
  ${pqComponents_SOURCE_DIR}
  ${pqComponents_BINARY_DIR}
  ${QtWidgets_SOURCE_DIR}
  ${QtWidgets_BINARY_DIR}
  ${QT_QTNETWORK_INCLUDE_DIR}
  )

FIND_PACKAGE(Qt4)
SET(QT_USE_QTNETWORK TRUE)
INCLUDE(${QT_USE_FILE})
  
# On Linux we build the plugin and it's dependencies 
if(APPLE)
 #  Copy libVisTrailsPlugin.dylib to  /Applications/ParaView 3.8.0.app/Contents/Plugins/
#  find_library(VISTRAILS_PLUGIN VisTrailsPlugin)
  
#  SET(PARAVIEW_PLUGINLIST ${PARAVIEW_PLUGINLIST} VisTrailsPlugin CACHE INTERNAL
#        "List of configured plugins")

#  file(COPY ${VISTRAILS_PLUGIN} DESTINATION ${ParaView_BINARY_DIR}/bin)

  #INSTALL(FILES ${VISTRAILS_PLUGIN}
  #    DESTINATION ${PV_INSTALL_PLUGIN_DIR}
  #    PERMISSIONS OWNER_WRITE OWNER_READ OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ
  #    COMPONENT Runtime)

  QT4_WRAP_CPP(MOC_SRCS PluginMain.h ToolBarStub.h)

  ADD_PARAVIEW_ACTION_GROUP(TB_IFACES TB_SRCS
                            CLASS_NAME ToolBarStub
                            GROUP_NAME "ToolBar/VisTrails")

  ADD_PARAVIEW_AUTO_START(AS_IFACES AS_SRCS
              CLASS_NAME PluginMain
              STARTUP Startup
              SHUTDOWN Shutdown)

  ADD_PARAVIEW_PLUGIN(VisTrailsPlugin "0.2"
                      GUI_INTERFACES ${AS_IFACES} ${TB_IFACES}
                      SOURCES ${MOC_SRCS} ${AS_SRCS} ${TB_SRCS}
                      PluginMain.cxx PluginMain.h
                      ToolBarStub.cxx ToolBarStub.h
                      ResourceData.h)
                      
  # Copy VisTrailsParaViewPlugin.app to /Applications
  find_file(VISTRAILS_PLUGIN_APP VisTrailsParaViewPlugin.app)

# On Windows we install the prebuilt plugin
elseif(WIN32)

  find_path(VISTRAILS_DIR vistrails)

  #vistrails
  INSTALL(DIRECTORY ${VISTRAILS_DIR}
      DESTINATION ${PV_INSTALL_PLUGIN_DIR}
      USE_SOURCE_PERMISSIONS
      COMPONENT Runtime)

  QT4_WRAP_CPP(MOC_SRCS PluginMain.h ToolBarStub.h)

  ADD_PARAVIEW_ACTION_GROUP(TB_IFACES TB_SRCS
                            CLASS_NAME ToolBarStub
                            GROUP_NAME "ToolBar/VisTrails")

  ADD_PARAVIEW_AUTO_START(AS_IFACES AS_SRCS
              CLASS_NAME PluginMain
              STARTUP Startup
              SHUTDOWN Shutdown)

  ADD_PARAVIEW_PLUGIN(VisTrailsPlugin "0.2"
                      GUI_INTERFACES ${AS_IFACES} ${TB_IFACES}
                      SOURCES ${MOC_SRCS} ${AS_SRCS} ${TB_SRCS}
                      PluginMain.cxx PluginMain.h
                      ToolBarStub.cxx ToolBarStub.h
                      ResourceData.h)
      
  list(APPEND PARAVIEW_PLUGINLIST VisTrailsPlugin)

elseif(UNIX)
  QT4_WRAP_CPP(MOC_SRCS PluginMain.h ToolBarStub.h)

  ADD_PARAVIEW_ACTION_GROUP(TB_IFACES TB_SRCS
                            CLASS_NAME ToolBarStub
                            GROUP_NAME "ToolBar/VisTrails")

  ADD_PARAVIEW_AUTO_START(AS_IFACES AS_SRCS
              CLASS_NAME PluginMain
              STARTUP Startup
              SHUTDOWN Shutdown)

  ADD_PARAVIEW_PLUGIN(VisTrailsPlugin "0.2"
                      GUI_INTERFACES ${AS_IFACES} ${TB_IFACES}
                      SOURCES ${MOC_SRCS} ${AS_SRCS} ${TB_SRCS}
                      PluginMain.cxx PluginMain.h
                      ToolBarStub.cxx ToolBarStub.h
                      ResourceData.h)
                      
  INSTALL(DIRECTORY vistrails
    DESTINATION ${PV_INSTALL_PLUGIN_DIR}
    USE_SOURCE_PERMISSIONS
    COMPONENT Runtime)
  
endif() #if(win32)
