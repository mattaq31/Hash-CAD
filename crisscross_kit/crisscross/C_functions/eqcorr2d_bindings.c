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

// ---------------- Rotation helpers: prerotate B into contiguous row-major buffers ----------------
static void pack_to_contig_u8(const unsigned char* src, npy_intp H, npy_intp W,
                              npy_intp s0, npy_intp s1, unsigned char* dst) {
    for (npy_intp y=0; y<H; ++y) {
        const unsigned char* sp = src + y*s0;
        unsigned char* dp = dst + y*W;
        for (npy_intp x=0; x<W; ++x) dp[x] = sp[x*s1];
    }
}

static void rot90_u8(const unsigned char* src, npy_intp H, npy_intp W,
                     npy_intp s0, npy_intp s1, unsigned char* dst) {
    // dst shape: (W,H), clockwise 90°
    for (npy_intp y = 0; y < W; ++y) {
        unsigned char* dp = dst + y*H;
        for (npy_intp x = 0; x < H; ++x) {
            const unsigned char* sp = src + (H-1 - x)*s0 + y*s1;
            dp[x] = *sp;
        }
    }
}

static void rot180_u8(const unsigned char* src, npy_intp H, npy_intp W,
                      npy_intp s0, npy_intp s1, unsigned char* dst) {
    // dst shape: (H,W)
    for (npy_intp y = 0; y < H; ++y) {
        unsigned char* dp = dst + y*W;
        const unsigned char* sp = src + (H-1 - y)*s0 + (W-1)*s1;
        for (npy_intp x = 0; x < W; ++x) dp[x] = sp[-(ptrdiff_t)x*s1];
    }
}

static void rot270_u8(const unsigned char* src, npy_intp H, npy_intp W,
                      npy_intp s0, npy_intp s1, unsigned char* dst) {
    // dst shape: (W,H), clockwise 270° (i.e., 90° CCW)
    for (npy_intp y = 0; y < W; ++y) {
        unsigned char* dp = dst + y*H;
        for (npy_intp x = 0; x < H; ++x) {
            const unsigned char* sp = src + x*s0 + (W-1 - y)*s1;
            dp[x] = *sp;
        }
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
    int f0, f90, f180, f270, do_hist, do_full, do_worst, do_smart;
    if (!PyArg_ParseTuple(args, "OOpppppppp",
                          &seqA_obj, &seqB_obj,
                          &f0, &f90, &f180, &f270,
                          &do_hist, &do_full, &do_worst, &do_smart)) {
        return NULL;
    }
    /* fprintf(stderr, ">>> pimmelberger <<<\n");*/
    /* fflush(stderr);*/

    PyObject *A_fast = PySequence_Fast(seqA_obj, "A_list must be a sequence");
    if (!A_fast) return NULL;
    PyObject *B_fast = PySequence_Fast(seqB_obj, "B_list must be a sequence");
    if (!B_fast) { Py_DECREF(A_fast); return NULL; }

    Py_ssize_t nA = PySequence_Fast_GET_SIZE(A_fast);
    Py_ssize_t nB = PySequence_Fast_GET_SIZE(B_fast);
    PyObject **A_items = PySequence_Fast_ITEMS(A_fast);
    PyObject **B_items = PySequence_Fast_ITEMS(B_fast);

    // Determine requested output flags. In smart mode the caller wants
    // all four rotations to be present in the returned structure, but we
    // may choose to skip computing some quarter rotations per pair.
    int req0 = f0, req90 = f90, req180 = f180, req270 = f270;
    if (do_smart) {
        req0 = req90 = req180 = req270 = 1;
    }

    // Pre-scan A_list to detect if any A is truly 2D (Ha>=2 && Wa>=2).
    // Smart mode will compute quarter rotations only when either side is 2D.
    /* Mark A as "truly 2D" only when both dimensions >= 2.
     Smart-mode uses this to decide whether quarter rotations (90/270)
   of B might be needed for this A; if neither side is 2D we can skip
   expensive 90/270 rotations and compute only 0°/180°. */
    int anyA2D = 0;
    for (Py_ssize_t i = 0; i < nA; ++i) {
        PyArrayObject* A = (PyArrayObject*)A_items[i];
        if (!PyArray_Check(A) || PyArray_TYPE(A) != NPY_UINT8 || PyArray_NDIM(A) != 2) {
            PyErr_SetString(PyExc_TypeError, "A_list items must be 2D uint8 arrays");
            goto fail;
        }
        const npy_intp Ha = PyArray_DIM(A,0), Wa = PyArray_DIM(A,1);
        if (Ha >= 2 && Wa >= 2) { anyA2D = 1; break; }
    }

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
        if (req0)   { L0   = PyList_New(nA); if (!L0)   goto fail; }
        if (req90)  { L90  = PyList_New(nA); if (!L90)  goto fail; }
        if (req180) { L180 = PyList_New(nA); if (!L180) goto fail; }
        if (req270) { L270 = PyList_New(nA); if (!L270) goto fail; }
        for (Py_ssize_t i=0; i<nA; ++i) {
            if (req0)   { PyObject* row = PyList_New(nB); if (!row) goto fail; PyList_SET_ITEM(L0,   i, row); }
            if (req90)  { PyObject* row = PyList_New(nB); if (!row) goto fail; PyList_SET_ITEM(L90,  i, row); }
            if (req180) { PyObject* row = PyList_New(nB); if (!row) goto fail; PyList_SET_ITEM(L180, i, row); }
            if (req270) { PyObject* row = PyList_New(nB); if (!row) goto fail; PyList_SET_ITEM(L270, i, row); }
        }
    }

    // Pre-rotate and pack all B arrays into contiguous row-major buffers so that
    // we can always call the single 0° kernel with Bs0=Wk and Bs1=1.



    typedef struct {
        unsigned char *p0, *p90, *p180, *p270;
        npy_intp H0, W0, H90, W90, H180, W180, H270, W270;
    } RotPack;
    RotPack* packs = (RotPack*)calloc((size_t)nB, sizeof(RotPack));
    if (!packs) { PyErr_NoMemory(); goto fail_packs; }

    for (Py_ssize_t j=0; j<nB; ++j) {
        PyArrayObject* B = (PyArrayObject*)B_items[j];
        const unsigned char* Bp = (const unsigned char*)PyArray_DATA(B);
        const npy_intp Hb = PyArray_DIM(B,0), Wb = PyArray_DIM(B,1);
        const npy_intp Bs0 = PyArray_STRIDE(B,0), Bs1 = PyArray_STRIDE(B,1);
        // Always create contiguous 0° pack
        packs[j].H0 = Hb; packs[j].W0 = Wb;
        size_t sz0 = (size_t)(Hb * Wb);
        packs[j].p0 = (unsigned char*)malloc(sz0);
        if (!packs[j].p0) { PyErr_NoMemory(); goto fail_packs; }
        pack_to_contig_u8(Bp, Hb, Wb, Bs0, Bs1, packs[j].p0);
        // Decide whether quarter rotations might be needed for this B across any A
        const int B_is_2D = (Hb >= 2 && Wb >= 2);
        const int need_quarters_any = do_smart ? (anyA2D || B_is_2D) : 0;
        // Optional rotations
        if ((do_smart && need_quarters_any) || (!do_smart && req90)) {
            packs[j].H90 = Wb; packs[j].W90 = Hb;
            size_t sz = (size_t)(Hb * Wb);
            packs[j].p90 = (unsigned char*)malloc(sz);
            if (!packs[j].p90) { PyErr_NoMemory(); goto fail_packs; }
            rot90_u8(Bp, Hb, Wb, Bs0, Bs1, packs[j].p90);
        }
        // 180° is cheap; in smart mode we always prepare 180° because we
        // compute it for 1D patterns as well.
        if ((do_smart) || (!do_smart && req180)) {
            packs[j].H180 = Hb; packs[j].W180 = Wb;
            size_t sz = (size_t)(Hb * Wb);
            packs[j].p180 = (unsigned char*)malloc(sz);
            if (!packs[j].p180) { PyErr_NoMemory(); goto fail_packs; }
            rot180_u8(Bp, Hb, Wb, Bs0, Bs1, packs[j].p180);
        }
        if ((do_smart && need_quarters_any) || (!do_smart && req270)) {
            packs[j].H270 = Wb; packs[j].W270 = Hb;
            size_t sz = (size_t)(Hb * Wb);
            packs[j].p270 = (unsigned char*)malloc(sz);
            if (!packs[j].p270) { PyErr_NoMemory(); goto fail_packs; }
            rot270_u8(Bp, Hb, Wb, Bs0, Bs1, packs[j].p270);
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
                if (req0 && /* will allocate only if we actually compute */ 1) {
                    /* allocation deferred until we know compute flags below */
                }
                /* We'll allocate per-rotation arrays only when both requested and computed */
            }

            // Decide per-pair which rotations to compute (compute flags c*)
            const int A_is_2D = (Ha >= 2 && Wa >= 2);
            const int B_is_2D_pair = (Hb >= 2 && Wb >= 2);
            int c0 = req0, c90 = req90, c180 = req180, c270 = req270;
            if (do_smart) {
                const int need_quarters = (A_is_2D || B_is_2D_pair);
                c0 = 1; c180 = 1; c90 = need_quarters ? 1 : 0; c270 = need_quarters ? 1 : 0;
            }

            // Now allocate full-result arrays only for rotations that are both
            // requested (req*) and computed (c*). If a rotation is requested but
            // not computed, we'll store Py_None in its cell to preserve shape.
            if (do_full) {
                if (req0 && c0)   { npy_intp dims[2] = {Ho0, Wo0};   O0   = (PyArrayObject*)PyArray_Zeros(2, dims, PyArray_DescrFromType(NPY_INT32), 0); if (!O0) goto fail;   o0   = (int32_t*)PyArray_DATA(O0); }
                if (req90 && c90) { npy_intp dims[2] = {Ho90, Wo90}; O90  = (PyArrayObject*)PyArray_Zeros(2, dims, PyArray_DescrFromType(NPY_INT32), 0); if (!O90) goto fail;  o90  = (int32_t*)PyArray_DATA(O90); }
                if (req180 && c180){ npy_intp dims[2] = {Ho180, Wo180}; O180 = (PyArrayObject*)PyArray_Zeros(2, dims, PyArray_DescrFromType(NPY_INT32), 0); if (!O180) goto fail; o180 = (int32_t*)PyArray_DATA(O180); }
                if (req270 && c270){ npy_intp dims[2] = {Ho270, Wo270}; O270 = (PyArrayObject*)PyArray_Zeros(2, dims, PyArray_DescrFromType(NPY_INT32), 0); if (!O270) goto fail; o270 = (int32_t*)PyArray_DATA(O270); }
            }

            // Decide which rotations to compute (compute flags c*)
            const int DO_WORST = do_worst ? 1 : 0;

            if (do_hist && !do_full) {
                if (c0)   loop_rot0_hist(Ap,Ha,Wa,As0,As1, packs[j].p0,   packs[j].H0,   packs[j].W0,   /*Bs0*/packs[j].W0, /*Bs1*/1,
                                         hist, hdim, NULL, Ho0,  Wo0,   DO_WORST, i,j, WT);
                if (c90 && packs[j].p90)  loop_rot0_hist(Ap,Ha,Wa,As0,As1, packs[j].p90,  packs[j].H90,  packs[j].W90,  /*Bs0*/packs[j].W90,/*Bs1*/1,
                                         hist, hdim, NULL, Ho90, Wo90,  DO_WORST, i,j, WT);
                if (c180 && packs[j].p180) loop_rot0_hist(Ap,Ha,Wa,As0,As1, packs[j].p180, packs[j].H180, packs[j].W180, /*Bs0*/packs[j].W180,/*Bs1*/1,
                                         hist, hdim, NULL, Ho180,Wo180, DO_WORST, i,j, WT);
                if (c270 && packs[j].p270) loop_rot0_hist(Ap,Ha,Wa,As0,As1, packs[j].p270, packs[j].H270, packs[j].W270, /*Bs0*/packs[j].W270,/*Bs1*/1,
                                         hist, hdim, NULL, Ho270,Wo270, DO_WORST, i,j, WT);

            } else if (!do_hist && do_full) {
                if (c0)   loop_rot0_full(Ap,Ha,Wa,As0,As1, packs[j].p0,   packs[j].H0,   packs[j].W0,   /*Bs0*/packs[j].W0, /*Bs1*/1,
                                         NULL, 0, o0,   Ho0,  Wo0,   DO_WORST, i,j, WT);
                if (c90 && packs[j].p90)  loop_rot0_full(Ap,Ha,Wa,As0,As1, packs[j].p90,  packs[j].H90,  packs[j].W90,  /*Bs0*/packs[j].W90,/*Bs1*/1,
                                         NULL, 0, o90,  Ho90, Wo90,  DO_WORST, i,j, WT);
                if (c180 && packs[j].p180) loop_rot0_full(Ap,Ha,Wa,As0,As1, packs[j].p180, packs[j].H180, packs[j].W180, /*Bs0*/packs[j].W180,/*Bs1*/1,
                                         NULL, 0, o180, Ho180,Wo180,DO_WORST, i,j, WT);
                if (c270 && packs[j].p270) loop_rot0_full(Ap,Ha,Wa,As0,As1, packs[j].p270, packs[j].H270, packs[j].W270, /*Bs0*/packs[j].W270,/*Bs1*/1,
                                         NULL, 0, o270, Ho270,Wo270,DO_WORST, i,j, WT);

            } else if (do_hist && do_full) {
                if (c0)   loop_rot0_both(Ap,Ha,Wa,As0,As1, packs[j].p0,   packs[j].H0,   packs[j].W0,   /*Bs0*/packs[j].W0, /*Bs1*/1,
                                         hist, hdim, o0,   Ho0,  Wo0,   DO_WORST, i,j, WT);
                if (c90 && packs[j].p90)  loop_rot0_both(Ap,Ha,Wa,As0,As1, packs[j].p90,  packs[j].H90,  packs[j].W90,  /*Bs0*/packs[j].W90,/*Bs1*/1,
                                         hist, hdim, o90,  Ho90, Wo90,  DO_WORST, i,j, WT);
                if (c180 && packs[j].p180) loop_rot0_both(Ap,Ha,Wa,As0,As1, packs[j].p180, packs[j].H180, packs[j].W180, /*Bs0*/packs[j].W180,/*Bs1*/1,
                                         hist, hdim, o180, Ho180,Wo180,DO_WORST, i,j, WT);
                if (c270 && packs[j].p270) loop_rot0_both(Ap,Ha,Wa,As0,As1, packs[j].p270, packs[j].H270, packs[j].W270, /*Bs0*/packs[j].W270,/*Bs1*/1,
                                         hist, hdim, o270, Ho270,Wo270,DO_WORST, i,j, WT);
            }

            if (do_full) {
                if (req0) {
                    PyObject* row = PyList_GET_ITEM(L0, i);
                    if (c0) PyList_SET_ITEM(row, j, (PyObject*)O0);
                    else { Py_INCREF(Py_None); PyList_SET_ITEM(row, j, Py_None); }
                }
                if (req90) {
                    PyObject* row = PyList_GET_ITEM(L90, i);
                    if (c90 && packs[j].p90) PyList_SET_ITEM(row, j, (PyObject*)O90);
                    else { Py_INCREF(Py_None); PyList_SET_ITEM(row, j, Py_None); }
                }
                if (req180) {
                    PyObject* row = PyList_GET_ITEM(L180, i);
                    if (c180 && packs[j].p180) PyList_SET_ITEM(row, j, (PyObject*)O180);
                    else { Py_INCREF(Py_None); PyList_SET_ITEM(row, j, Py_None); }
                }
                if (req270) {
                    PyObject* row = PyList_GET_ITEM(L270, i);
                    if (c270 && packs[j].p270) PyList_SET_ITEM(row, j, (PyObject*)O270);
                    else { Py_INCREF(Py_None); PyList_SET_ITEM(row, j, Py_None); }
                }
            }
        }
    }

    PyObject* worst_pairs = do_worst ? WT->pairs : Py_None;
    Py_XINCREF(worst_pairs);

    Py_DECREF(A_fast); Py_DECREF(B_fast);
    if (do_worst) free(WT->seen);

    PyObject* ret = Py_BuildValue("OOOOOO",
        do_hist ? (PyObject*)Hist : Py_None,
        (do_full && req0)   ? L0   : Py_None,
        (do_full && req90)  ? L90  : Py_None,
        (do_full && req180) ? L180 : Py_None,
        (do_full && req270) ? L270 : Py_None,
        do_worst ? worst_pairs : Py_None);

    Py_XDECREF(Hist);
    if (do_worst) Py_XDECREF(worst_pairs);
    return ret;

fail_packs:
    if (packs) {
        for (Py_ssize_t k=0; k<nB; ++k) {
            if (packs[k].p0)   { free(packs[k].p0); packs[k].p0 = NULL; }
            if (packs[k].p90)  { free(packs[k].p90); packs[k].p90 = NULL; }
            if (packs[k].p180) { free(packs[k].p180); packs[k].p180 = NULL; }
            if (packs[k].p270) { free(packs[k].p270); packs[k].p270 = NULL; }
        }
        free(packs); packs = NULL;
    }

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
