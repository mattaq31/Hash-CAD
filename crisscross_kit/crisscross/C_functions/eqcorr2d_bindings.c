#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include "eqcorr2d.h"

// Forward declare module methods
static PyObject* eqcorr2d_compute(PyObject* self, PyObject* args);

// Generate wrappers referencing external loop kernels defined in eqcorr2d_core.c
#define DECL_WRAP(NAME) \
static inline void NAME##_hist( \
    const unsigned char* A, npy_intp Ha, npy_intp Wa, npy_intp As0, npy_intp As1, \
    const unsigned char* B, npy_intp Hb, npy_intp Wb, npy_intp Bs0, npy_intp Bs1, \
    long long* hist, npy_intp hist_len, int32_t* out, npy_intp Ho, npy_intp Wo, \
    const int DO_WORST, Py_ssize_t IA, Py_ssize_t IB, worst_tracker_t* WT) { \
    NAME##_mode(A,Ha,Wa,As0,As1, B,Hb,Wb,Bs0,Bs1, \
                hist, hist_len, NULL, Ho,Wo, \
                1, 0, DO_WORST, IA,IB, WT); } \
static inline void NAME##_full( \
    const unsigned char* A, npy_intp Ha, npy_intp Wa, npy_intp As0, npy_intp As1, \
    const unsigned char* B, npy_intp Hb, npy_intp Wb, npy_intp Bs0, npy_intp Bs1, \
    long long* hist, npy_intp hist_len, int32_t* out, npy_intp Ho, npy_intp Wo, \
    const int DO_WORST, Py_ssize_t IA, Py_ssize_t IB, worst_tracker_t* WT) { \
    NAME##_mode(A,Ha,Wa,As0,As1, B,Hb,Wb,Bs0,Bs1, \
                NULL, 0, out, Ho,Wo, \
                0, 1, DO_WORST, IA,IB, WT); } \
static inline void NAME##_both( \
    const unsigned char* A, npy_intp Ha, npy_intp Wa, npy_intp As0, npy_intp As1, \
    const unsigned char* B, npy_intp Hb, npy_intp Wb, npy_intp Bs0, npy_intp Bs1, \
    long long* hist, npy_intp hist_len, int32_t* out, npy_intp Ho, npy_intp Wo, \
    const int DO_WORST, Py_ssize_t IA, Py_ssize_t IB, worst_tracker_t* WT) { \
    NAME##_mode(A,Ha,Wa,As0,As1, B,Hb,Wb,Bs0,Bs1, \
                hist, hist_len, out, Ho,Wo, \
                1, 1, DO_WORST, IA,IB, WT); }

// Bring in the external symbol names from the core implementation
void loop_rot0_mode(
    const unsigned char*, npy_intp, npy_intp, npy_intp, npy_intp,
    const unsigned char*, npy_intp, npy_intp, npy_intp, npy_intp,
    long long*, npy_intp, int32_t*, npy_intp, npy_intp,
    const int, const int, const int, Py_ssize_t, Py_ssize_t, worst_tracker_t*);
void loop_rot90_mode(
    const unsigned char*, npy_intp, npy_intp, npy_intp, npy_intp,
    const unsigned char*, npy_intp, npy_intp, npy_intp, npy_intp,
    long long*, npy_intp, int32_t*, npy_intp, npy_intp,
    const int, const int, const int, Py_ssize_t, Py_ssize_t, worst_tracker_t*);
void loop_rot180_mode(
    const unsigned char*, npy_intp, npy_intp, npy_intp, npy_intp,
    const unsigned char*, npy_intp, npy_intp, npy_intp, npy_intp,
    long long*, npy_intp, int32_t*, npy_intp, npy_intp,
    const int, const int, const int, Py_ssize_t, Py_ssize_t, worst_tracker_t*);
void loop_rot270_mode(
    const unsigned char*, npy_intp, npy_intp, npy_intp, npy_intp,
    const unsigned char*, npy_intp, npy_intp, npy_intp, npy_intp,
    long long*, npy_intp, int32_t*, npy_intp, npy_intp,
    const int, const int, const int, Py_ssize_t, Py_ssize_t, worst_tracker_t*);

// Instantiate wrappers for the 4 rotations
DECL_WRAP(loop_rot0)
DECL_WRAP(loop_rot90)
DECL_WRAP(loop_rot180)
DECL_WRAP(loop_rot270)
#undef DECL_WRAP

// ------------------ main API moved here ------------------
/* ---------------------------------------------------------------------------------------
 * Main callable from Python: eqcorr2d.compute(...)
 *
 * High-level idea
 * ---------------
 * We’re doing a “2D equality correlation” (like convolution, but instead of
 * multiply+sum we count how many positions are exactly equal). Zeros are
 * treated as “don’t care” and never contribute (i.e., a==0 or b==0 -> no match).
 *
 * Inputs from Python
 * ------------------
 * - A_list: sequence of NumPy arrays, each uint8 and 2D (row-major recommended).
 * - B_list: same structure as A_list.
 *   Hint: if you have 1D row vectors, convert to shape (1, L).
 *
 * Flags (all Python bools/ints)
 * ----------------------------
 * - rot0, rot90, rot180, rot270: which rotations of B to compute.
 *   Rotation definition (clockwise): see rotation comments in eqcorr2d_core.c.
 * - do_hist: if 1, accumulate a global histogram of “number of matches per offset”.
 *   Histogram length is max(Hb*Wb)+1 over all B in B_list (index == match count).
 * - do_full: if 1, also return the full 2D result map for every pair/rotation.
 *   Shapes: 0°/180° => (Ha+Hb-1, Wa+Wb-1); 90°/270° => (Ha+Wb-1, Wa+Hb-1).
 *   Warning: can be large; returns nested Python list [nA][nB] of np.int32 arrays.
 * - report_worst: if 1, track the global maximum match count observed and return
 *   unique (iA, iB) pairs that achieved it across all requested rotations.
 *
 * Return value (6-tuple)
 * ----------------------
 * ( hist_or_None,
 *   outs0_or_None, outs90_or_None, outs180_or_None, outs270_or_None,
 *   worst_pairs_or_None )
 *
 * Implementation notes
 * --------------------
 * - This binding translates Python/NumPy objects into raw views and drives the
 *   pure-C kernels in eqcorr2d_core.c. It is the only layer that allocates
 *   Python objects and manages reference counts.
 * - The hot loops are in the core and do not touch the Python C-API.
 * ------------------------------------------------------------------------------------- */
static PyObject* eqcorr2d_compute(PyObject* self, PyObject* args)
{
    PyObject *seqA_obj, *seqB_obj;
    int f0, f90, f180, f270, do_hist, do_full, do_worst;
    if (!PyArg_ParseTuple(args, "OOppppppp",
                          &seqA_obj, &seqB_obj,
                          &f0, &f90, &f180, &f270,
                          &do_hist, &do_full, &do_worst)) {
        return NULL;
    }

    PyObject *A_fast = PySequence_Fast(seqA_obj, "A_list must be a sequence");
    if (!A_fast) return NULL;
    PyObject *B_fast = PySequence_Fast(seqB_obj, "B_list must be a sequence");
    if (!B_fast) { Py_DECREF(A_fast); return NULL; }

    Py_ssize_t nA = PySequence_Fast_GET_SIZE(A_fast);
    Py_ssize_t nB = PySequence_Fast_GET_SIZE(B_fast);
    PyObject **A_items = PySequence_Fast_ITEMS(A_fast);
    PyObject **B_items = PySequence_Fast_ITEMS(B_fast);

    npy_intp max_prod = 0;
    for (Py_ssize_t j=0; j<nB; ++j) {
        PyArrayObject* B = (PyArrayObject*)B_items[j];
        npy_intp Hb = PyArray_DIM(B,0), Wb = PyArray_DIM(B,1);
        npy_intp prod = Hb * Wb;
        if (prod > max_prod) max_prod = prod;
    }
    if (max_prod < 1) max_prod = 1;
    npy_intp hdim = max_prod + 1;

    PyArrayObject* Hist = NULL;   long long* hist = NULL;
    if (do_hist) {
        Hist = (PyArrayObject*)PyArray_Zeros(1, &hdim, PyArray_DescrFromType(NPY_INT64), 0);
        if (!Hist) { Py_DECREF(A_fast); Py_DECREF(B_fast); return NULL; }
        hist = (long long*)PyArray_DATA(Hist);
    }

    worst_tracker_t WT_local; worst_tracker_t* WT = NULL;
    if (do_worst) {
        WT = &WT_local;
        WT->max_val = INT_MIN; WT->nA = nA; WT->nB = nB;
        WT->pairs = PyList_New(0);
        if (!WT->pairs) { Py_DECREF(A_fast); Py_DECREF(B_fast); Py_XDECREF(Hist); return NULL; }
        WT->seen = (unsigned char*)calloc((size_t)(nA * nB), 1);
        if (!WT->seen) { Py_DECREF(A_fast); Py_DECREF(B_fast); Py_XDECREF(Hist); Py_DECREF(WT->pairs); return PyErr_NoMemory(); }
    }

    PyObject *L0 = Py_None, *L90 = Py_None, *L180 = Py_None, *L270 = Py_None;
    if (do_full) {
        if (f0)   { L0   = PyList_New(nA); if (!L0)   goto fail; }
        if (f90)  { L90  = PyList_New(nA); if (!L90)  goto fail; }
        if (f180) { L180 = PyList_New(nA); if (!L180) goto fail; }
        if (f270) { L270 = PyList_New(nA); if (!L270) goto fail; }
        for (Py_ssize_t i=0; i<nA; ++i) {
            if (f0)   { PyObject* row = PyList_New(nB); if (!row) goto fail; PyList_SET_ITEM(L0,   i, row); }
            if (f90)  { PyObject* row = PyList_New(nB); if (!row) goto fail; PyList_SET_ITEM(L90,  i, row); }
            if (f180) { PyObject* row = PyList_New(nB); if (!row) goto fail; PyList_SET_ITEM(L180, i, row); }
            if (f270) { PyObject* row = PyList_New(nB); if (!row) goto fail; PyList_SET_ITEM(L270, i, row); }
        }
    }

    for (Py_ssize_t i=0; i<nA; ++i) {
        PyArrayObject* A = (PyArrayObject*)A_items[i];
        if (!PyArray_Check(A) || PyArray_TYPE(A)!=NPY_UINT8 || PyArray_NDIM(A)!=2) { PyErr_SetString(PyExc_TypeError, "A_list items must be 2D uint8 arrays"); goto fail; }
        const unsigned char* Ap = (const unsigned char*)PyArray_DATA(A);
        const npy_intp Ha = PyArray_DIM(A,0), Wa = PyArray_DIM(A,1);
        const npy_intp As0 = PyArray_STRIDE(A,0), As1 = PyArray_STRIDE(A,1);

        for (Py_ssize_t j=0; j<nB; ++j) {
            PyArrayObject* B = (PyArrayObject*)B_items[j];
            if (!PyArray_Check(B) || PyArray_TYPE(B)!=NPY_UINT8 || PyArray_NDIM(B)!=2) { PyErr_SetString(PyExc_TypeError, "B_list items must be 2D uint8 arrays"); goto fail; }
            const unsigned char* Bp = (const unsigned char*)PyArray_DATA(B);
            const npy_intp Hb = PyArray_DIM(B,0), Wb = PyArray_DIM(B,1);
            const npy_intp Bs0 = PyArray_STRIDE(B,0), Bs1 = PyArray_STRIDE(B,1);

            // Output sizes for each rotation
            const npy_intp Ho0 = Ha + Hb - 1, Wo0 = Wa + Wb - 1;
            const npy_intp Ho180 = Ho0, Wo180 = Wo0;
            const npy_intp Ho90 = Ha + Wb - 1, Wo90 = Wa + Hb - 1;
            const npy_intp Ho270 = Ho90, Wo270 = Wo90;

            PyArrayObject *O0=NULL,*O90=NULL,*O180=NULL,*O270=NULL;
            int32_t *o0=NULL,*o90=NULL,*o180=NULL,*o270=NULL;
            if (do_full) {
                if (f0)   { npy_intp dims[2] = {Ho0, Wo0};   O0   = (PyArrayObject*)PyArray_Zeros(2, dims, PyArray_DescrFromType(NPY_INT32), 0); if (!O0) goto fail;   o0   = (int32_t*)PyArray_DATA(O0); }
                if (f90)  { npy_intp dims[2] = {Ho90, Wo90}; O90  = (PyArrayObject*)PyArray_Zeros(2, dims, PyArray_DescrFromType(NPY_INT32), 0); if (!O90) goto fail;  o90  = (int32_t*)PyArray_DATA(O90); }
                if (f180) { npy_intp dims[2] = {Ho180, Wo180}; O180 = (PyArrayObject*)PyArray_Zeros(2, dims, PyArray_DescrFromType(NPY_INT32), 0); if (!O180) goto fail; o180 = (int32_t*)PyArray_DATA(O180); }
                if (f270) { npy_intp dims[2] = {Ho270, Wo270}; O270 = (PyArrayObject*)PyArray_Zeros(2, dims, PyArray_DescrFromType(NPY_INT32), 0); if (!O270) goto fail; o270 = (int32_t*)PyArray_DATA(O270); }
            }

            // Dispatch per rotation with selected outputs
            const int DO_WORST = do_worst ? 1 : 0;
            if (do_hist && !do_full) {
                if (f0)   loop_rot0_hist  (Ap,Ha,Wa,As0,As1, Bp,Hb,Wb,Bs0,Bs1, hist, hdim, NULL, Ho0,Wo0,   DO_WORST, i,j, WT);
                if (f90)  loop_rot90_hist (Ap,Ha,Wa,As0,As1, Bp,Hb,Wb,Bs0,Bs1, hist, hdim, NULL, Ho90,Wo90, DO_WORST, i,j, WT);
                if (f180) loop_rot180_hist(Ap,Ha,Wa,As0,As1, Bp,Hb,Wb,Bs0,Bs1, hist, hdim, NULL, Ho180,Wo180,DO_WORST, i,j, WT);
                if (f270) loop_rot270_hist(Ap,Ha,Wa,As0,As1, Bp,Hb,Wb,Bs0,Bs1, hist, hdim, NULL, Ho270,Wo270,DO_WORST, i,j, WT);
            } else if (!do_hist && do_full) {
                if (f0)   loop_rot0_full  (Ap,Ha,Wa,As0,As1, Bp,Hb,Wb,Bs0,Bs1, NULL, 0, o0, Ho0,Wo0,   DO_WORST, i,j, WT);
                if (f90)  loop_rot90_full (Ap,Ha,Wa,As0,As1, Bp,Hb,Wb,Bs0,Bs1, NULL, 0, o90, Ho90,Wo90, DO_WORST, i,j, WT);
                if (f180) loop_rot180_full(Ap,Ha,Wa,As0,As1, Bp,Hb,Wb,Bs0,Bs1, NULL, 0, o180, Ho180,Wo180,DO_WORST, i,j, WT);
                if (f270) loop_rot270_full(Ap,Ha,Wa,As0,As1, Bp,Hb,Wb,Bs0,Bs1, NULL, 0, o270, Ho270,Wo270,DO_WORST, i,j, WT);
            } else if (do_hist && do_full) {
                if (f0)   loop_rot0_both  (Ap,Ha,Wa,As0,As1, Bp,Hb,Wb,Bs0,Bs1, hist, hdim, o0, Ho0,Wo0,   DO_WORST, i,j, WT);
                if (f90)  loop_rot90_both (Ap,Ha,Wa,As0,As1, Bp,Hb,Wb,Bs0,Bs1, hist, hdim, o90, Ho90,Wo90, DO_WORST, i,j, WT);
                if (f180) loop_rot180_both(Ap,Ha,Wa,As0,As1, Bp,Hb,Wb,Bs0,Bs1, hist, hdim, o180, Ho180,Wo180,DO_WORST, i,j, WT);
                if (f270) loop_rot270_both(Ap,Ha,Wa,As0,As1, Bp,Hb,Wb,Bs0,Bs1, hist, hdim, o270, Ho270,Wo270,DO_WORST, i,j, WT);
            }

            if (do_full) {
                if (f0)   { PyObject* row = PyList_GET_ITEM(L0, i);   PyList_SET_ITEM(row, j, (PyObject*)O0); }
                if (f90)  { PyObject* row = PyList_GET_ITEM(L90, i);  PyList_SET_ITEM(row, j, (PyObject*)O90); }
                if (f180) { PyObject* row = PyList_GET_ITEM(L180, i); PyList_SET_ITEM(row, j, (PyObject*)O180); }
                if (f270) { PyObject* row = PyList_GET_ITEM(L270, i); PyList_SET_ITEM(row, j, (PyObject*)O270); }
            }
        }
    }

    PyObject* worst_pairs = do_worst ? WT->pairs : Py_None;
    Py_XINCREF(worst_pairs);

    Py_DECREF(A_fast); Py_DECREF(B_fast);
    if (do_worst) free(WT->seen);

    PyObject* ret = Py_BuildValue("OOOOOO",
        do_hist ? (PyObject*)Hist : Py_None,
        (do_full && f0)   ? L0   : Py_None,
        (do_full && f90)  ? L90  : Py_None,
        (do_full && f180) ? L180 : Py_None,
        (do_full && f270) ? L270 : Py_None,
        do_worst ? worst_pairs : Py_None);

    Py_XDECREF(Hist);
    if (do_worst) Py_XDECREF(worst_pairs);
    return ret;

fail:
    Py_XDECREF(Hist);
    if (do_worst) { Py_XDECREF(WT->pairs); free(WT->seen); }
    Py_DECREF(A_fast); Py_DECREF(B_fast);
    return NULL;
}

static PyMethodDef Eqcorr2dMethods[] = {
    {"compute", (PyCFunction)eqcorr2d_compute, METH_VARARGS, "Compute eqcorr2d"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "eqcorr2d",
    "eqcorr2d module",
    -1,
    Eqcorr2dMethods
};

PyMODINIT_FUNC PyInit_eqcorr2d(void)
{
    import_array();
    return PyModule_Create(&moduledef);
}
