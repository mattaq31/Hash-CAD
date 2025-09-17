// main.c — Small C entry point that embeds Python and drives eqcorr2d via integration_functions.wrap_eqcorr2d
// Purpose: enable stepping into crisscross_kit/crisscross/C_functions/eqcorr2d.c while running inside CLion.
// Strategy: Initialize Python, adjust sys.path to include the build directory (for eqcorr2d.pyd)
// and the project package root (for crisscross and integration_functions), then execute a
// short Python snippet that builds small 2D arrays and calls wrap_eqcorr2d(...).

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdio.h>
#include <stdlib.h>

static void print_py_error(const char* context) {
    if (PyErr_Occurred()) {
        fprintf(stderr, "Python error during %s\n", context);
        PyErr_Print();
    }
}

int main(int argc, char** argv) {
    // 1) Initialize the Python interpreter
    Py_Initialize();

    // Ensure we have a default program name (helps on Windows)
    wchar_t* prog = Py_DecodeLocale("eqcorr2d_main", NULL);
    if (prog) {
        Py_SetProgramName(prog);
    }

    // 2) Import and call a tiny Python driver instead of embedding a long string.
    //    Keep sys.path minimal so both the built eqcorr2d.pyd and the project package are importable.
    int rc = 0;

    // Insert build dir (.) and project package root (..\\crisscross_kit) into sys.path
    {
        PyObject* sys_path = PySys_GetObject("path"); // borrowed ref
        if (sys_path) {
            PyObject* dot = PyUnicode_FromString(".");
            if (dot) { PyList_Insert(sys_path, 0, dot); Py_DECREF(dot); }
            PyObject* proj = PyUnicode_FromString("..\\crisscross_kit");
            if (proj) { PyList_Insert(sys_path, 0, proj); Py_DECREF(proj); }
        }
    }

    // Import module and call function: crisscross.C_functions.debug_driver.debug_entry()
    PyObject* pName = PyUnicode_FromString("crisscross.C_functions.debug_driver");
    if (!pName) {
        fprintf(stderr, "[C] Failed to create unicode for module name\n");
        print_py_error("PyUnicode_FromString(module)");
        rc = -1; goto finalize;
    }
    PyObject* pModule = PyImport_Import(pName);
    Py_DECREF(pName);
    if (!pModule) {
        fprintf(stderr, "[C] Failed to import crisscross.C_functions.debug_driver\n");
        print_py_error("PyImport_Import(debug_driver)");
        rc = -1; goto finalize;
    }

    PyObject* pFunc = PyObject_GetAttrString(pModule, "debug_entry");
    if (!pFunc || !PyCallable_Check(pFunc)) {
        fprintf(stderr, "[C] debug_entry not found or not callable\n");
        print_py_error("GetAttr debug_entry");
        Py_XDECREF(pFunc);
        Py_DECREF(pModule);
        rc = -1; goto finalize;
    }

    PyObject* pRes = PyObject_CallObject(pFunc, NULL);
    if (!pRes) {
        fprintf(stderr, "[C] debug_entry raised an exception\n");
        print_py_error("Call debug_entry");
        Py_DECREF(pFunc);
        Py_DECREF(pModule);
        rc = -1; goto finalize;
    }
    Py_DECREF(pRes);
    Py_DECREF(pFunc);
    Py_DECREF(pModule);

finalize: ;

    // 3) Finalize Python
    if (Py_FinalizeEx() < 0) {
        fprintf(stderr, "Py_FinalizeEx failed\n");
    }

    if (prog) {
        PyMem_RawFree(prog);
    }

    return rc == 0 ? 0 : 1;
}
