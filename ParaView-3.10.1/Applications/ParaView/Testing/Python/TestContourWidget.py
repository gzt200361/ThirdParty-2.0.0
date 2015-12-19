#/usr/bin/env python

import QtTesting

object1 = 'pqClientMainWindow/menubar/menuSources'
QtTesting.playCommand(object1, 'activate', 'RTAnalyticSource')
object2 = 'pqClientMainWindow/proxyTabDock/proxyTabWidget/qt_tabwidget_stackedwidget/objectInspector/Accept'
QtTesting.playCommand(object2, 'activate', '')
object3 = 'pqClientMainWindow/menubar/menuFilters/Common'
QtTesting.playCommand(object3, 'activate', 'Contour')
QtTesting.playCommand(object2, 'activate', '')
object5 = 'pqClientMainWindow/proxyTabDock/proxyTabWidget/qt_tabwidget_stackedwidget/objectInspector/ScrollArea/qt_scrollarea_viewport/PanelArea/Editor/1pqCollapsedGroup1/pqSampleScalarWidget'
QtTesting.setProperty(object5, 'samples', '120')
QtTesting.playCommand(object2, 'activate', '')
QtTesting.setProperty(object5, 'samples', '120;130;140;150')
QtTesting.playCommand(object2, 'activate', '')
object1 = 'pqClientMainWindow/menubar/menu_Edit'
QtTesting.playCommand(object1, 'activate', 'actionEditUndo')
# Need to wait a moment to allow the GUI to update.
import time
time.sleep(1)
val = QtTesting.getProperty(object5, 'samples')

if val != "120":
    import exceptions
    raise exceptions.RuntimeError, "Expecting 120, received: " + val
else:
    print "Value comparison successful -- Test passed."
