/*=========================================================================

   Program: ParaView
   Module:    pqSaveAnimationGeometryReaction.cxx

   Copyright (c) 2005,2006 Sandia Corporation, Kitware Inc.
   All rights reserved.

   ParaView is a free software; you can redistribute it and/or modify it
   under the terms of the ParaView license version 1.2. 

   See License_v1.2.txt for the full ParaView license.
   A copy of this license can be obtained by contacting
   Kitware Inc.
   28 Corporate Drive
   Clifton Park, NY 12065
   USA

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

========================================================================*/
#include "pqSaveAnimationGeometryReaction.h"

#include "pqActiveObjects.h"
#include "pqAnimationManager.h"
#include "pqPVApplicationCore.h"
#include "pqCoreUtilities.h"
#include "pqFileDialog.h"

#include <QDebug>

//-----------------------------------------------------------------------------
pqSaveAnimationGeometryReaction::pqSaveAnimationGeometryReaction(
  QAction* parentObject): Superclass(parentObject)
{
  // load state enable state depends on whether we are connected to an active
  // server or not and whether
  pqActiveObjects* activeObjects = &pqActiveObjects::instance();
  QObject::connect(activeObjects, SIGNAL(serverChanged(pqServer*)),
    this, SLOT(updateEnableState()));
  QObject::connect(activeObjects, SIGNAL(viewChanged(pqView*)),
    this, SLOT(updateEnableState()));
  this->updateEnableState();
}

//-----------------------------------------------------------------------------
void pqSaveAnimationGeometryReaction::updateEnableState()
{
  pqActiveObjects* activeObjects = &pqActiveObjects::instance();
  bool is_enabled = (activeObjects->activeServer() != NULL &&
    activeObjects->activeView() != NULL);
  this->parentAction()->setEnabled(is_enabled);
}

//-----------------------------------------------------------------------------
void pqSaveAnimationGeometryReaction::saveAnimationGeometry()
{
  pqAnimationManager* mgr = pqPVApplicationCore::instance()->animationManager();
  if (!mgr || !mgr->getActiveScene())
    {
    qDebug() << "Cannot save animation since no active scene is present.";
    return;
    }

  pqView* view = pqActiveObjects::instance().activeView();
  if (!view)
    {
    qDebug() << "Cannot save animation geometry since no active view.";
    return;
    }

  QString filters = "ParaView Data files (*.pvd);;All files (*)";
  pqFileDialog fileDialog (pqActiveObjects::instance().activeServer(),
    pqCoreUtilities::mainWidget(),
    tr("Save Animation Geometry"), 
    QString(), 
    filters);
  fileDialog.setObjectName("FileSaveAnimationDialog");
  fileDialog.setFileMode(pqFileDialog::AnyFile);
  if (fileDialog.exec() == QDialog::Accepted)
    {
    pqSaveAnimationGeometryReaction::saveAnimationGeometry(
      fileDialog.getSelectedFiles()[0]);
    }
}

//-----------------------------------------------------------------------------
void pqSaveAnimationGeometryReaction::saveAnimationGeometry(
  const QString& filename)
{
  pqAnimationManager* mgr = pqPVApplicationCore::instance()->animationManager();
  if (!mgr || !mgr->getActiveScene())
    {
    qDebug() << "Cannot save animation since no active scene is present.";
    return;
    }

  pqView* view = pqActiveObjects::instance().activeView();
  if (!view)
    {
    qDebug() << "Cannot save animation geometry since no active view.";
    return;
    }

  if (!mgr->saveGeometry(filename, view))
    {
    qDebug() << "Animation save geometry failed!";
    }
}
