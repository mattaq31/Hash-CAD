// main.c — Small C entry point that embeds Python and drives eqcorr2d via integration_functions.wrap_eqcorr2d
// Purpose: enable stepping into crisscross_kit/crisscross/C_functions/eqcorr2d.c while running inside CLion.
// Strategy: Initialize Python, adjust sys.path to include the build directory (for eqcorr2d.pyd)
// and the project package root (for crisscross and integration_functions), then execute a
// short Python snippet that builds small 2D arrays and calls wrap_eqcorr2d(...).

#define PY_SSIZE_T_CLEAN
#include <Python.h>

int main(int argc, char** argv) {
    Py_Initialize();

    /* Prepend import paths so the built extension and package are importable */
    PyObject *sys = PyImport_ImportModule("sys");
    PyObject *path = sys ? PyObject_GetAttrString(sys, "path") : NULL;
    if (path && PyList_Check(path)) {
        PyObject *p0 = PyUnicode_FromString(".");
        PyList_Insert(path, 0, p0);
        Py_XDECREF(p0);
        PyObject *p1 = PyUnicode_FromString(".\\crisscross_kit\\crisscross\\C_functions");
        PyList_Insert(path, 1, p1);
        Py_XDECREF(p1);
    }
    Py_XDECREF(path);
    Py_XDECREF(sys);

    /* Import the Python debug driver and call debug_entry() */
    PyObject *mod = PyImport_ImportModule("crisscross.C_functions.debug_driver");
    PyObject *entry = mod ? PyObject_GetAttrString(mod, "debug_entry") : NULL;
    PyObject *res = NULL;
    if (entry && PyCallable_Check(entry)) {
        res = PyObject_CallObject(entry, NULL);
    }

    /* Clean up safely (use Py_XDECREF to avoid crashes on NULL pointers) */
    Py_XDECREF(res);
    Py_XDECREF(entry);
    Py_XDECREF(mod);

    Py_FinalizeEx();
    return 0;
}
