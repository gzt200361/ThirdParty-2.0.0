
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

from auto_gen import DBVistrail as _DBVistrail
from auto_gen import DBAdd, DBChange, DBDelete, DBAbstractionRef, DBGroup, \
    DBModule
from id_scope import IdScope

class DBVistrail(_DBVistrail):
    def __init__(self, *args, **kwargs):
	_DBVistrail.__init__(self, *args, **kwargs)
        self.idScope = IdScope(remap={DBAdd.vtType: 'operation',
                                      DBChange.vtType: 'operation',
                                      DBDelete.vtType: 'operation',
                                      DBAbstractionRef.vtType: DBModule.vtType,
                                      DBGroup.vtType: DBModule.vtType})

        self.idScope.setBeginId('action', 1)
        self.db_objects = {}

        # keep a reference to the current logging information here
        self.log_filename = None
        self.log = None

    def db_add_object(self, obj):
        self.db_objects[(obj.vtType, obj.db_id)] = obj

    def db_get_object(self, type, id):
        return self.db_objects.get((type, id), None)

    def db_update_object(self, obj, **kwargs):
        # want to swap out old object with a new version
        # need this for updating aliases...
        # hack it using setattr...
        real_obj = self.db_objects[(obj.vtType, obj.db_id)]
        for (k, v) in kwargs.iteritems():
            if hasattr(real_obj, k):
                setattr(real_obj, k, v)
