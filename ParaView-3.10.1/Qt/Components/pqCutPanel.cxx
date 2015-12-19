/*=========================================================================

   Program: ParaView
   Module:    pqCutPanel.cxx

   Copyright (c) 2005-2008 Sandia Corporation, Kitware Inc.
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

=========================================================================*/
#include "pqCutPanel.h"

#include "pqCollapsedGroup.h"
#include "pqPipelineFilter.h"
#include "pqPropertyManager.h"
#include "pqSampleScalarWidget.h"
#include "vtkSMDoubleVectorProperty.h"

#include <QVBoxLayout>

//////////////////////////////////////////////////////////////////////////////
// pqCutPanel::pqImplementation

class pqCutPanel::pqImplementation
{
public:
  pqImplementation() :
    SampleScalarWidget(false)
  {
  }
  
  /// Controls the number and position of "slices"
  pqSampleScalarWidget SampleScalarWidget;
};

pqCutPanel::pqCutPanel(pqProxy* object_proxy, QWidget* p) :
  Superclass(object_proxy, p),
  Implementation(new pqImplementation())
{
  pqCollapsedGroup* const group2 = new pqCollapsedGroup(this);
  group2->setTitle(tr(this->proxy()->GetProperty("ContourValues")->GetXMLLabel()));
  QVBoxLayout* l = new QVBoxLayout(group2);
  this->Implementation->SampleScalarWidget.layout()->setMargin(0);
  l->addWidget(&this->Implementation->SampleScalarWidget);
 
  QGridLayout* const panel_layout = this->PanelLayout;
  int rowCount = panel_layout->rowCount()-2;

  // delete the widgets added by pqAutoGeneratedObjectPanel for the
  // ContourValues since they are inappropriate.
  delete this->findChild<QWidget*>("_labelForContourValues");
  delete this->findChild<QWidget*>("ContourValues_0");

  panel_layout->addWidget(group2, rowCount, 0, 1, panel_layout->columnCount());
  //panel_layout->setRowStretch(panel_layout->rowCount(), 1);
  
  // Link SampleScalarWidget's qProperty to vtkSMProperty
  this->propertyManager()->registerLink(
    &this->Implementation->SampleScalarWidget, "samples",
    SIGNAL(samplesChanged()), this->proxy(),
    this->proxy()->GetProperty("ContourValues"));
  
  QObject::connect(
    this->propertyManager(), SIGNAL(accepted()), this, SLOT(onAccepted()));
    
  QObject::connect(
    this->propertyManager(), SIGNAL(rejected()), this, SLOT(onRejected()));

  // Setup the sample scalar widget ...
  this->Implementation->SampleScalarWidget.setDataSources(
    this->proxy(),
    vtkSMDoubleVectorProperty::SafeDownCast(this->proxy()->GetProperty("ContourValues")));
}

pqCutPanel::~pqCutPanel()
{
  delete this->Implementation;
}

void pqCutPanel::onAccepted()
{
  this->Implementation->SampleScalarWidget.accept();
}

void pqCutPanel::onRejected()
{
  this->Implementation->SampleScalarWidget.reset();
}

