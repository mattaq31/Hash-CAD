#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include "eqcorr2d.h"
#include <stddef.h>
#include <limits.h>
// Forward declare module methods
static PyObject* eqcorr2d_compute(PyObject* self, PyObject* args);

// We only use the 0° core kernel and pre-rotate B into contiguous buffers.
// The core declaration is provided by eqcorr2d.h, so no redundant declaration here.

static inline void loop_rot0_hist(
    const u8* A, npy_intp Ha, npy_intp Wa, npy_intp As0, npy_intp As1,
    const u8* B, npy_intp Hb, npy_intp Wb, npy_intp Bs0, npy_intp Bs1,
    hist_t* hist, npy_intp hist_len, out_t* out, npy_intp Ho, npy_intp Wo,
    int DO_WORST, npy_intp IA, npy_intp IB, worst_tracker_t* WT) {
    loop_rot0_mode(A,Ha,Wa,As0,As1, B,Hb,Wb,Bs0,Bs1,
                   hist, hist_len, NULL, Ho,Wo,
                   1, 0, DO_WORST, IA,IB, WT);
}
static inline void loop_rot0_full(
    const u8* A, npy_intp Ha, npy_intp Wa, npy_intp As0, npy_intp As1,
    const u8* B, npy_intp Hb, npy_intp Wb, npy_intp Bs0, npy_intp Bs1,
    hist_t* hist, npy_intp hist_len, out_t* out, npy_intp Ho, npy_intp Wo,
    int DO_WORST, npy_intp IA, npy_intp IB, worst_tracker_t* WT) {
    loop_rot0_mode(A,Ha,Wa,As0,As1, B,Hb,Wb,Bs0,Bs1,
                   NULL, 0, out, Ho,Wo,
                   0, 1, DO_WORST, IA,IB, WT);
}
static inline void loop_rot0_both(
    const u8* A, npy_intp Ha, npy_intp Wa, npy_intp As0, npy_intp As1,
    const u8* B, npy_intp Hb, npy_intp Wb, npy_intp Bs0, npy_intp Bs1,
    hist_t* hist, npy_intp hist_len, out_t* out, npy_intp Ho, npy_intp Wo,
    int DO_WORST, npy_intp IA, npy_intp IB, worst_tracker_t* WT) {
    loop_rot0_mode(A,Ha,Wa,As0,As1, B,Hb,Wb,Bs0,Bs1,
                   hist, hist_len, out, Ho,Wo,
                   1, 1, DO_WORST, IA,IB, WT);
}

// ---------------- Pack B into contiguous row‑major buffers (no rotation ----------------
static void pack_to_contig_u8(const unsigned char* src, npy_intp H, npy_intp W,
                              npy_intp s0, npy_intp s1, unsigned char* dst) {
    for (npy_intp y=0; y<H; ++y) {
        const unsigned char* sp = src + y*s0;
        unsigned char* dp = dst + y*W;
        for (npy_intp x=0; x<W; ++x) dp[x] = sp[x*s1];
    }
}


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
 * - B_list: same structure as A_list. If you need rotations (90/180/270), do it
 *   in Python beforehand by rotating B and calling this function separately.
 *   Hint: if you have 1D row vectors, convert to shape (1, L).
 * - compute_instructions (mask): 2D uint8 array of shape (nA, nB). Entry [i,j]==1
 *   means: compute A_list[i] vs B_list[j]; 0 means: skip this pair.
 * - do_hist (int bool): if 1, accumulate a global histogram of “number of matches
 *   per offset”. Histogram length is max(Hb*Wb)+1 over all B in B_list (bin=index).
 * - do_full (int bool): if 1, also return the full 2D result map for every
 *   computed pair. Shape at 0°: (Ha+Hb-1, Wa+Wb-1). Warning: can be large; returns
 *   nested Python list [nA][nB] of np.int32 arrays (with None for skipped pairs).
 * - report_worst (int bool): if 1, track the global maximum match count observed
 *   and return unique (iA, iB) pairs that achieved it.
 *
 * Return value (3-tuple)
 * ----------------------
 * ( hist_or_None,
 *   outs0_or_None,
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
    PyObject *seqA_obj, *seqB_obj, *mask_obj;
    int do_hist, do_full, do_worst;
    if (!PyArg_ParseTuple(args, "OOOppp",
                          &seqA_obj, &seqB_obj, &mask_obj,
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

    // Validate arrays and compute histogram length (max Hb*Wb + 1)
    npy_intp max_prod = 0;
    for (Py_ssize_t i = 0; i < nA; ++i) {
        PyArrayObject* A = (PyArrayObject*)A_items[i];
        if (!PyArray_Check(A) || PyArray_TYPE(A) != NPY_UINT8 || PyArray_NDIM(A) != 2) {
            PyErr_SetString(PyExc_TypeError, "A_list items must be 2D uint8 arrays");
            goto fail;
        }
    }
    for (Py_ssize_t j=0; j<nB; ++j) {
        PyArrayObject* B = (PyArrayObject*)B_items[j];
        if (!PyArray_Check(B) || PyArray_TYPE(B) != NPY_UINT8 || PyArray_NDIM(B) != 2) {
            PyErr_SetString(PyExc_TypeError, "B_list items must be 2D uint8 arrays");
            goto fail;
        }
        npy_intp Hb = PyArray_DIM(B,0), Wb = PyArray_DIM(B,1);
        npy_intp prod = Hb * Wb;
        if (prod > max_prod) max_prod = prod;
    }
    if (max_prod < 1) max_prod = 1;
    npy_intp hdim = max_prod + 1;

    // Validate compute_instructions mask: expect 2D array (nA x nB) of bool/uint8/int
    PyArrayObject* Mask = (PyArrayObject*)PyArray_FROM_OTF(mask_obj, NPY_UINT8, NPY_ARRAY_ALIGNED);
    if (!Mask) { goto fail; }
    if (PyArray_NDIM(Mask) != 2) {
        Py_DECREF(Mask); PyErr_SetString(PyExc_ValueError, "compute_instructions must be a 2D array (nA x nB)"); goto fail; }
    if (PyArray_DIM(Mask,0) != nA || PyArray_DIM(Mask,1) != nB) {
        Py_DECREF(Mask); PyErr_SetString(PyExc_ValueError, "compute_instructions shape must be (len(A_list), len(B_list))"); goto fail; }
    const u8* maskp = (const u8*)PyArray_DATA(Mask);
    npy_intp m_s0 = PyArray_STRIDE(Mask,0);
    npy_intp m_s1 = PyArray_STRIDE(Mask,1);

    PyArrayObject* Hist = NULL;   long long* hist = NULL;
    if (do_hist) {
        Hist = (PyArrayObject*)PyArray_Zeros(1, &hdim, PyArray_DescrFromType(NPY_INT64), 0);
        if (!Hist) { Py_DECREF(A_fast); Py_DECREF(B_fast); Py_DECREF(Mask); return NULL; }
        hist = (long long*)PyArray_DATA(Hist);
    }

    worst_tracker_t WT_local; worst_tracker_t* WT = NULL;
    if (do_worst) {
        WT = &WT_local;
        WT->max_val = INT_MIN; WT->nA = nA; WT->nB = nB;
        WT->pairs = PyList_New(0);
        if (!WT->pairs) { Py_DECREF(A_fast); Py_DECREF(B_fast); Py_XDECREF(Hist); Py_DECREF(Mask); return NULL; }
        WT->seen = (unsigned char*)calloc((size_t)(nA * nB), 1);
        if (!WT->seen) { Py_DECREF(A_fast); Py_DECREF(B_fast); Py_XDECREF(Hist); Py_DECREF(WT->pairs); Py_DECREF(Mask); return PyErr_NoMemory(); }
    }

    // Only r0 is produced; other rotation outputs are None in the return tuple
    PyObject *L0 = Py_None;
    if (do_full) {
        L0 = PyList_New(nA); if (!L0) goto fail;
        for (Py_ssize_t i=0; i<nA; ++i) {
            PyObject* row = PyList_New(nB); if (!row) goto fail; PyList_SET_ITEM(L0, i, row);
        }
    }

    // Pack B into contiguous buffers for fast kernel
    typedef struct { unsigned char *p0; npy_intp H0,W0; } Pack;
    Pack* packs = (Pack*)calloc((size_t)nB, sizeof(Pack));
    if (!packs) { PyErr_NoMemory(); goto fail_packs; }
    for (Py_ssize_t j=0; j<nB; ++j) {
        PyArrayObject* B = (PyArrayObject*)B_items[j];
        const unsigned char* Bp = (const unsigned char*)PyArray_DATA(B);
        const npy_intp Hb = PyArray_DIM(B,0), Wb = PyArray_DIM(B,1);
        const npy_intp Bs0 = PyArray_STRIDE(B,0), Bs1 = PyArray_STRIDE(B,1);
        packs[j].H0 = Hb; packs[j].W0 = Wb;
        size_t sz0 = (size_t)(Hb * Wb);
        packs[j].p0 = (unsigned char*)malloc(sz0);
        if (!packs[j].p0) { PyErr_NoMemory(); goto fail_packs; }
        pack_to_contig_u8(Bp, Hb, Wb, Bs0, Bs1, packs[j].p0);
    }

    const int DO_WORST = do_worst ? 1 : 0;
    for (Py_ssize_t i=0; i<nA; ++i) {
        PyArrayObject* A = (PyArrayObject*)A_items[i];
        const unsigned char* Ap = (const unsigned char*)PyArray_DATA(A);
        const npy_intp Ha = PyArray_DIM(A,0), Wa = PyArray_DIM(A,1);
        const npy_intp As0 = PyArray_STRIDE(A,0), As1 = PyArray_STRIDE(A,1);
        for (Py_ssize_t j=0; j<nB; ++j) {
            // mask check: skip pair if mask[i,j]==0
            const u8 mj = *(const u8*)((const char*)maskp + i*m_s0 + j*m_s1);
            if (!mj) {
                if (do_full) {
                    PyObject* row = PyList_GET_ITEM(L0, i);
                    Py_INCREF(Py_None); PyList_SET_ITEM(row, j, Py_None);
                }
                continue;
            }
            PyArrayObject* B = (PyArrayObject*)B_items[j];
            const npy_intp Hb = PyArray_DIM(B,0), Wb = PyArray_DIM(B,1);
            const npy_intp Ho0 = Ha + Hb - 1, Wo0 = Wa + Wb - 1;

            PyArrayObject *O0=NULL; int32_t *o0=NULL;
            if (do_full) { npy_intp dims[2] = {Ho0, Wo0}; O0=(PyArrayObject*)PyArray_Zeros(2,dims,PyArray_DescrFromType(NPY_INT32),0); if (!O0) goto fail; o0=(int32_t*)PyArray_DATA(O0); }

            if (do_hist && !do_full) {
                loop_rot0_hist(Ap,Ha,Wa,As0,As1, packs[j].p0, packs[j].H0, packs[j].W0, packs[j].W0, 1,
                               hist, hdim, NULL, Ho0, Wo0, DO_WORST, i,j, WT);
            } else if (!do_hist && do_full) {
                loop_rot0_full(Ap,Ha,Wa,As0,As1, packs[j].p0, packs[j].H0, packs[j].W0, packs[j].W0, 1,
                               NULL, 0, o0, Ho0, Wo0, DO_WORST, i,j, WT);
            } else if (do_hist && do_full) {
                loop_rot0_both(Ap,Ha,Wa,As0,As1, packs[j].p0, packs[j].H0, packs[j].W0, packs[j].W0, 1,
                               hist, hdim, o0, Ho0, Wo0, DO_WORST, i,j, WT);
            }

            if (do_full) {
                PyObject* row = PyList_GET_ITEM(L0, i);
                PyList_SET_ITEM(row, j, (PyObject*)O0);
            }
        }
    }

    // Free contiguous B packs now that kernels are done
    if (packs) {
        for (Py_ssize_t k=0; k<nB; ++k) {
            if (packs[k].p0) { free(packs[k].p0); packs[k].p0 = NULL; }
        }
        free(packs); packs = NULL;
    }

    PyObject* worst_pairs = do_worst ? WT->pairs : Py_None;
    Py_XINCREF(worst_pairs);

    Py_DECREF(A_fast); Py_DECREF(B_fast); Py_DECREF(Mask);
    if (do_worst) free(WT->seen);

    PyObject* ret = Py_BuildValue("OOO",
        do_hist ? (PyObject*)Hist : Py_None,
        do_full ? L0 : Py_None,
        do_worst ? worst_pairs : Py_None);

    Py_XDECREF(Hist);
    if (do_worst) Py_XDECREF(worst_pairs);
    return ret;

fail_packs:
    if (packs) {
        for (Py_ssize_t k=0; k<nB; ++k) {
            if (packs[k].p0)   { free(packs[k].p0); packs[k].p0 = NULL; }
        }
        free(packs); packs = NULL;
    }

fail:
    // On failure, ensure all allocations are released
    if (packs) {
        for (Py_ssize_t k=0; k<nB; ++k) {
            if (packs[k].p0) { free(packs[k].p0); packs[k].p0 = NULL; }
        }
        free(packs); packs = NULL;
    }
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
    "eqcorr2d_engine",
    "eqcorr2d_engine module",
    -1,
    Eqcorr2dMethods
};

PyMODINIT_FUNC PyInit_eqcorr2d_engine(void)
{
    import_array();
    return PyModule_Create(&moduledef);
}
