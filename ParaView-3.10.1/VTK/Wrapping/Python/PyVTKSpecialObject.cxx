/*=========================================================================

  Program:   Visualization Toolkit
  Module:    PyVTKSpecialObject.cxx

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================*/
/*-----------------------------------------------------------------------
  The PyVTKSpecialObject was created in Feb 2001 by David Gobbi.
  It was substantially updated in April 2010 by David Gobbi.

  A PyVTKSpecialObject is a python object that represents an object
  that belongs to one of the special classes in VTK, that is, classes
  that are not derived from vtkObjectBase.  Unlike vtkObjects, these
  special objects are not reference counted: a PyVTKSpecialObject
  always contains its own copy of the C++ object.

  The PyVTKSpecialType is a simple structure that contains information
  about the PyVTKSpecialObject type that cannot be stored in python's
  PyTypeObject struct.  Each PyVTKSpecialObject contains a pointer to
  its PyVTKSpecialType. The PyVTKSpecialTypes are also stored in a map
  in vtkPythonUtil.cxx, so that they can be lookup up by name.
-----------------------------------------------------------------------*/

#include "PyVTKSpecialObject.h"
#include "vtkPythonUtil.h"

#include <vtksys/ios/sstream>

// Silence warning like
// "dereferencing type-punned pointer will break strict-aliasing rules"
// it happens because this kind of expression: (long *)&ptr
// pragma GCC diagnostic is available since gcc>=4.2
#if defined(__GNUG__) && (__GNUC__>4) || (__GNUC__==4 && __GNUC_MINOR__>=2)
#pragma GCC diagnostic ignored "-Wstrict-aliasing"
#endif

//--------------------------------------------------------------------
PyVTKSpecialType::PyVTKSpecialType(
    PyTypeObject *typeobj, PyMethodDef *cmethods, PyMethodDef *ccons,
    const char *cdocs[], PyVTKSpecialCopyFunc copyfunc)
{
  this->py_type = typeobj;
  this->methods = cmethods;
  this->constructors = ccons;
  this->docstring = vtkPythonUtil::BuildDocString(cdocs);
  this->copy_func = copyfunc;
}

//--------------------------------------------------------------------
#if PY_VERSION_HEX < 0x02020000
PyObject *PyVTKSpecialObject_GetAttr(PyObject *self, PyObject *attr)
{
  PyVTKSpecialObject *obj = (PyVTKSpecialObject *)self;
  char *name = PyString_AsString(attr);
  PyMethodDef *meth;

  if (name[0] == '_')
    {
    if (strcmp(name, "__name__") == 0)
      {
      return PyString_FromString(self->ob_type->tp_name);
      }
    if (strcmp(name, "__doc__") == 0)
      {
      Py_INCREF(obj->vtk_info->docstring);
      return obj->vtk_info->docstring;
      }
    if (strcmp(name,"__methods__") == 0)
      {
      meth = obj->vtk_info->methods;
      PyObject *lst;
      int i, n;

      for (n = 0; meth && meth[n].ml_name; n++)
        {
        ;
        }

      if ((lst = PyList_New(n)) != NULL)
        {
        meth = obj->vtk_info->methods;
        for (i = 0; i < n; i++)
          {
          PyList_SetItem(lst, i, PyString_FromString(meth[i].ml_name));
          }
        PyList_Sort(lst);
        }
      return lst;
      }

    if (strcmp(name, "__members__") == 0)
      {
      PyObject *lst;
      if ((lst = PyList_New(4)) != NULL)
        {
        PyList_SetItem(lst, 0, PyString_FromString("__doc__"));
        PyList_SetItem(lst, 1, PyString_FromString("__members__"));
        PyList_SetItem(lst, 2, PyString_FromString("__methods__"));
        PyList_SetItem(lst, 3, PyString_FromString("__name__"));
        }
      return lst;
      }
    }

  for (meth = obj->vtk_info->methods; meth && meth->ml_name; meth++)
    {
    if (strcmp(name, meth->ml_name) == 0)
      {
      return PyCFunction_New(meth, self);
      }
    }

  PyErr_SetString(PyExc_AttributeError, name);
  return NULL;
}
#endif

//--------------------------------------------------------------------
PyObject *PyVTKSpecialObject_New(const char *classname, void *ptr)
{
  // would be nice if "info" could be passed instead if "classname",
  // but this way of doing things is more dynamic if less efficient
  PyVTKSpecialType *info = vtkPythonUtil::FindSpecialType(classname);

#if PY_MAJOR_VERSION >= 2
  PyVTKSpecialObject *self = PyObject_New(PyVTKSpecialObject, info->py_type);
#else
  PyVTKSpecialObject *self = PyObject_NEW(PyVTKSpecialObject, info->py_type);
#endif

  self->vtk_info = info;
  self->vtk_ptr = ptr;
  self->vtk_hash = -1;

  return (PyObject *)self;
}

//--------------------------------------------------------------------
PyObject *PyVTKSpecialObject_CopyNew(const char *classname, const void *ptr)
{
  PyVTKSpecialType *info = vtkPythonUtil::FindSpecialType(classname);

  if (info == 0)
    {
    char buf[256];
    sprintf(buf,"cannot create object of unknown type \"%s\"",classname);
    PyErr_SetString(PyExc_ValueError,buf);
    return NULL;
    }

#if PY_MAJOR_VERSION >= 2
  PyVTKSpecialObject *self = PyObject_New(PyVTKSpecialObject, info->py_type);
#else
  PyVTKSpecialObject *self = PyObject_NEW(PyVTKSpecialObject, info->py_type);
#endif

  self->vtk_info = info;
  self->vtk_ptr = info->copy_func(ptr);
  self->vtk_hash = -1;

  return (PyObject *)self;
}

//--------------------------------------------------------------------
PyObject *PyVTKSpecialType_New(PyTypeObject *pytype,
  PyMethodDef *methods, PyMethodDef *constructors, PyMethodDef *newmethod,
  const char *docstring[], PyVTKSpecialCopyFunc copyfunc)
{
  // Add this type to the special type map
  PyVTKSpecialType *info =
    vtkPythonUtil::AddSpecialTypeToMap(
      pytype, methods, constructors, docstring, copyfunc);

  if (info)
    {
    // Add the built docstring to the type
    pytype->tp_doc = PyString_AsString(info->docstring);
    newmethod->ml_doc = PyString_AsString(info->docstring);
    }

  // Return a generator function for python < 2.2,
  // return the type object itself for python >= 2.2
#if PY_VERSION_HEX < 0x2020000
  return PyCFunction_New(newmethod, Py_None);
#else
  return (PyObject *)pytype;
#endif
}
