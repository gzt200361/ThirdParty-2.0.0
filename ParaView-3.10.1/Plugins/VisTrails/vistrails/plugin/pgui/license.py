
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
## Copyright (C) 2008, 2009 VisTrails, Inc. All rights reserved.
##
############################################################################
from PyQt4 import QtGui, QtCore
import plugin.pgui.resources.images_rc
import CaptureAPI
import sys

def postInvalidLicenseMsg():
    """ postInvalidLicenseMsg() -> None
 
    """
    app = QtGui.QApplication(sys.argv)
    msg = QtGui.QMessageBox(QtGui.QMessageBox.NoIcon, "License Error",
                            "Your VisTrails Provenance Explorer "
                            "license is invalid or has expired!")
    msg.show()
    app.exec_()
    
def checkLicense(daysRemaining):
    """ checkLicense(daysRemaining: int) -> int
    Pop open a dialog before main app has been initialized."
    """
    app = QtGui.QApplication(sys.argv)
    dialog = QLicenseDialog(None, daysRemaining)
    dialog.show()
    app.exec_()
    return (dialog.result(), dialog.getKey())
    
class QLicenseDialog(QtGui.QDialog):
    """ Build the GUI for checking licenses """
    def __init__(self, parent=None, daysRemaining=0):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.blocking = False
        self.setModal(True)
        self.setWindowTitle('Provenance Explorer Pro Evaluation')
        layout = QtGui.QVBoxLayout(self)
        self.setLayout(layout)

        self.introLabel = QtGui.QLabel('<html><b>Welcome to VisTrails Provenance '
                                       'Explorer Pro Evaluation</b>')
        self.introLabel.setAlignment(QtCore.Qt.AlignHCenter)
        layout.addWidget(self.introLabel)
        
        hLayout = QtGui.QHBoxLayout(self)
        layout.addLayout(hLayout)

        import plugin.app.resources.images_rc
        self.appPixmap = QtGui.QPixmap(':/images/app_icon.png')
        self.appPixmap = self.appPixmap.scaled(64,64)
        self.appLogo = QtGui.QLabel()
        self.appLogo.setPixmap(self.appPixmap)
        self.appLogo.setAlignment(QtCore.Qt.AlignHCenter)
        self.appURL = QtGui.QLabel('<html><a href=\"http:\\\\www.vistrails.com\">www.vistrails.com<\a></html>')
        self.appURL.setAlignment(QtCore.Qt.AlignHCenter)
        logoLayout = QtGui.QVBoxLayout(self)
        hLayout.addLayout(logoLayout)
        
        logoLayout.addWidget(self.appLogo)
        logoLayout.addWidget(self.appURL)

        messageLayout = QtGui.QVBoxLayout(self)
        hLayout.addLayout(messageLayout)

        self.trialLabel = QtGui.QLabel()
        if daysRemaining == 1:
            self.trialLabel.setText('You have 1 day '
                                    'remaining on your trial.')
        elif daysRemaining:
            self.trialLabel.setText('You have ' + str(daysRemaining) + ' days '
                                    'remaining on your trial.')
        else:
            self.trialLabel.setText('Your trial has expired. '
                                    'To continue using this plug-in\n'
                                    'enter a software key.')
        
        messageLayout.addWidget(self.trialLabel)
        
        self.optionsGroup = QtGui.QButtonGroup(self)
        self.trialRB = QtGui.QRadioButton('Continue with evaluation')
        self.keyRB = QtGui.QRadioButton('Enter a Software Key')
        self.optionsGroup.addButton(self.trialRB)
        self.optionsGroup.addButton(self.keyRB)
        
        messageLayout.addWidget(self.trialRB)
        messageLayout.addWidget(self.keyRB)
        
        keyLayout = QtGui.QHBoxLayout(self)
        layout.addLayout(keyLayout)        
        
        self.softwareKeyLabel = QtGui.QLabel('Software Key:')
        keyLayout.addWidget(self.softwareKeyLabel)
        keyLayout.setSpacing(2)
        self.keyFields = []
        for i in range(4):
            keyField = QtGui.QTextEdit(self)
            keyField.setAcceptRichText(False)
            keyField.setLineWrapMode(QtGui.QTextEdit.NoWrap)
            keyField.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            keyField.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            keyField.setTabChangesFocus(True)
            keyField.setMaximumHeight(20)
            keyField.setMaximumWidth(50)
            self.keyFields.append(keyField)
            keyLayout.addWidget(keyField)
            if i < 3:
                keyLayout.addWidget(QtGui.QLabel('-'))

         # A space
        layout.addSpacing(10)

        # Then the buttons
        bLayout = QtGui.QHBoxLayout()
        layout.addLayout(bLayout)
        bLayout.addStretch()

        self.okButton = QtGui.QPushButton('Ok')
        bLayout.addWidget(self.okButton)
        
        self.cancelButton = QtGui.QPushButton('Cancel')
        bLayout.addWidget(self.cancelButton)
        bLayout.addStretch()

        # Connect buttons to dialog handlers
        self.connect(self.okButton, QtCore.SIGNAL('clicked()'),
                     self.accept)
        self.connect(self.cancelButton, QtCore.SIGNAL('clicked()'),
                     self.reject)
        self.connect(self.trialRB, QtCore.SIGNAL('toggled(bool)'),
                     self.trialToggled)
        self.connect(self.keyRB, QtCore.SIGNAL('toggled(bool)'),
                     self.keyToggled)
        for i in range(4):
            self.connect(self.keyFields[i], QtCore.SIGNAL('textChanged()'),
                     self.keyFieldChanged)
                     
        # Setup some initial widget state
        if daysRemaining:
            self.trialRB.setChecked(True)
            self.softwareKeyLabel.setEnabled(False)
            for i in range(4):
                self.keyFields[i].setEnabled(False)
        else:
            self.keyRB.setChecked(True)
            self.trialRB.setEnabled(False)
            self.okButton.setEnabled(False)

    def accept(self):
        """ accept() -> None 
        
        """
        QtGui.QDialog.accept(self)

    def reject(self):
        """ reject() -> None 

        """
        QtGui.QDialog.reject(self)

    def keyToggled(self, checked):
        """ keyToggled(checked: bool) -> None 

        """
        if checked:
            self.softwareKeyLabel.setEnabled(True)
            done = True
            for i in range(4):
                self.keyFields[i].setEnabled(True)
                key = self.keyFields[i].toPlainText()
                if len(key) != 4:
                    done = False
            if not done:
                self.okButton.setEnabled(False)

    def trialToggled(self, checked):
        """ trialToggled(checked: bool) -> None
        
        """
        if checked:
            self.softwareKeyLabel.setEnabled(False)
            for i in range(4):
                self.keyFields[i].setEnabled(False)
            self.okButton.setEnabled(True)

    def keyFieldChanged(self):
        if self.blocking:
            return
        self.blocking = True
        done = True
        for i in range(4):
            cursor = self.keyFields[i].textCursor()
            cursorPos = cursor.position()
            key = self.keyFields[i].toPlainText()
            key = key.toUpper()
            if len(key) > 4:
                key.truncate(4)
                cursorPos = 4
            elif len(key) < 4:
                done = False
            self.keyFields[i].setText(key)
            cursor.setPosition(cursorPos)
            self.keyFields[i].setTextCursor(cursor)
        if done:
            self.okButton.setEnabled(True)
        else:
            self.okButton.setEnabled(False)
        self.blocking = False

    def getKey(self):
        """
        """
        key = ""
        for i in range(4):
            key = key + self.keyFields[i].toPlainText()
        if len(key) == 16:
            return key
        else:
            return ""
