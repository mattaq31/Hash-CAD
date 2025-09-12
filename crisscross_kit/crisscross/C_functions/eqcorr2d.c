// eqcorr2d.c  — DO_HIST/DO_FULL compile-time mode; zeros ignored; API extended with report_worst
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <numpy/arrayobject.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

#ifdef _OPENMP
#include <omp.h>
#endif



/* ---------------------------------------------------------------------------------------
 * Main callable from Python: eqcorr2d.compute(...)
 *
 * High-level idea
 * ---------------
 * We’re doing a “2D equality correlation” (like convolution, but instead of multiply+sum
 * we count how many positions are exactly equal). Zeros are treated as “don’t care” and
 * never contribute (i.e., a==0 or b==0 -> no match).
 *
 * The small pattern B is slid over A at every possible offset (including partial overlap
 * around the borders). We can do this for 0°, 90°, 180°, 270° rotations of B.
 *
 * What Python passes in
 * ---------------------
 * - A_list: a Python sequence (e.g., list) of NumPy arrays, each **uint8** and **2D**.
 * - B_list: same as A_list (sequence of **uint8** 2D arrays).
 *            Hint: if you have 1D row vectors, convert to shape (1, L).
 *
 * Flags (all Python bools/ints, parsed as 'p' here)
 * ------------------------------------------------
 * - rot0, rot90, rot180, rot270:
 *     Which rotations of B to compute. 1 = compute, 0 = skip.
 *     Rotation definition:
 *       0°   : as stored
 *       90°  : quarter-turn clockwise
 *       180° : upside down
 *       270° : quarter-turn counter-clockwise
 *
 * - do_hist:
 *     If 1, we accumulate a global histogram of “number of matches per offset”.
 *     The histogram length is max(Hb*Wb) + 1 over all B in B_list (index == match count).
 *
 * - do_full:
 *     If 1, we also return the full 2D result map for **every pair** (A_i, B_j) for each
 *     requested rotation. For rotation r, the output shape is:
 *        r in {0°,180°}: (Ha + Hb - 1,  Wa + Wb - 1)
 *        r in {90°,270°}: (Ha + Wb - 1,  Wa + Hb - 1)
 *     Warning: this returns a nested Python list of size [nA][nB], each entry a NumPy
 *              array int32. This can be very large in memory if nA, nB, or shapes grow.
 *
 * - report_worst:
 *     If 1, we track the **maximum** match count seen at any offset and any rotation.
 *     We return a Python list of (iA, iB) index pairs that achieved this global maximum
 *     (duplicates removed; iA = index in A_list, iB = index in B_list).
 *     If 0, we return None in that slot.
 *
 * What we return to Python (6-tuple)
 * ----------------------------------
 * ( hist_or_None,
 *   outs0_or_None,
 *   outs90_or_None,
 *   outs180_or_None,
 *   outs270_or_None,
 *   worst_pairs_or_None )
 *
 * - hist_or_None         : np.int64 1D array of length max(Hb*Wb)+1, or None if do_hist=0.
 * - outs*_or_None        : If do_full=1 and the rotation was requested, a Python list of
 *                          length nA, each item is a list of length nB, each entry is a
 *                          2D np.int32 array with the per-offset match counts. Otherwise None.
 * - worst_pairs_or_None  : If report_worst=1, a Python list of (iA, iB) tuples that achieved
 *                          the **global** maximum across all rotations and offsets; else None.
 *
 * ------------------------------------------------------------------------------------- */


/* ---- worst_tracker_t -----------------------------------------------------
 * Define a struct to track which (iA, iB) pairs hit the GLOBAL max match count.
 *
 * Fields:
 *   max_val : current global maximum (start very low).
 *   nA, nB  : sizes of A_list and B_list (for indexing).
 *   seen    : nA*nB bitmap; seen[iA*nB + iB] == 1 means that pair is already
 *             added for the CURRENT max (avoids duplicates).
 *   pairs   : Python list of (iA, iB) tuples that achieved the CURRENT max.
 *
 * Usage:
 *   - Helper functions reset the tracker when a new max is found
 *     (clear pairs + zero seen).
 *   - On ties with max_val, a new (iA, iB) is appended if not seen before.
 *
 * Lifetime:
 *   - Struct is stack-local; `seen` is calloc’d and later free’d.
 *   - `pairs` is a Python list; its ref is transferred into the return tuple.
 * ------------------------------------------------------------------------- */
typedef struct {
    int           max_val;
    Py_ssize_t    nA, nB;
    unsigned char* seen;
    PyObject*     pairs;
} worst_tracker_t;



/* worst_reset
 * Purpose: Start fresh when we discover a STRICTLY larger maximum match.
 *
 * What it does:
 *   - Set wt->max_val = new_max.
 *   - Zero the 'seen' bitmap (so the next (iA,iB) we add for this new max
 *     won’t be treated as a duplicate from the old max).
 *   - Empty the Python list 'pairs' so it only holds pairs for this new max.
 *
 * Params:
 *   wt       : tracker to reset (must have nA, nB set; seen may be NULL).
 *   new_max  : the new global maximum match count.
 *
 * Returns:
 *   0  on success,
 *  -1 if clearing the Python list fails (rare; we ignore in hot paths).
 */
static inline int worst_reset(worst_tracker_t* wt, int new_max) {
    wt->max_val = new_max;
    if (wt->seen) memset(wt->seen, 0, (size_t)(wt->nA * wt->nB));
    if (!wt->pairs) return 0;
    /* Clear list: PyList_SetSlice(list, 0, PyList_GET_SIZE(list), NULL) */
    if (PyList_SetSlice(wt->pairs, 0, PyList_GET_SIZE(wt->pairs), NULL) < 0) return -1;
    return 0;
}

/* Add (ia, ib) pair to the worst-tracker if not already recorded */
static inline int worst_add_if_new(worst_tracker_t* wt, Py_ssize_t ia, Py_ssize_t ib) {
    if (!wt->pairs || !wt->seen) return 0;     /* safety: tracker not active */
    Py_ssize_t idx = ia * wt->nB + ib;         /* flatten (ia, ib) into 1D index */
    if (wt->seen[idx]) return 0;               /* already seen → skip */
    wt->seen[idx] = 1;                         /* mark as recorded */
    PyObject* tup = Py_BuildValue("(nn)", ia, ib); /* build Python tuple (ia, ib) */
    if (!tup) return -1;                       /* fail if tuple allocation fails */
    int rc = PyList_Append(wt->pairs, tup);    /* append to Python list */
    Py_DECREF(tup);                            /* drop local ref (list keeps its own) */
    return rc;                                 /* return Python API result code */
}

/* ----------------------------------------------------------------------
 * loop_rot0_mode — one A–B pair at 0° rotation
 *
 * What it does
 * ------------
 * Slides B over A at every offset (ox, oy). For each overlap window,
 * counts matches of equal, non-zero entries (acc). Optionally:
 *   - adds acc to a global histogram,
 *   - writes acc into the full 2D output map,
 *   - updates a global “worst” tracker (max acc seen; stores (IA, IB) pairs).
 *
 * Inputs (this call handles ONE pair A_list[IA] vs B_list[IB])
 * -----------------------------------------------------------
 *   A,B    : pointers to the 2D uint8 arrays (single elements from the Python lists)
 *   Ha,Wa  : A's height, width
 *   Hb,Wb  : B's height, width
 *   As0,As1: byte-strides for A (row step, col step)
 *   Bs0,Bs1: byte-strides for B
 *   Ho,Wo  : output map size for this rotation
 *
 * Optional outputs / side effects
 * -------------------------------
 *   hist,hist_len : global histogram buffer and its length (bin = acc)
 *   out           : per-offset map (int32), size Ho×Wo
 *   WT            : worst-pair tracker (tracks global max acc and the (IA,IB) that hit it)
 *
 * Control flags & indices
 * -----------------------
 *   DO_HIST  : 1 -> increment histogram bin for acc
 *   DO_FULL  : 1 -> write acc into out[oy,ox]
 *   DO_WORST : 1 -> compare acc to WT->max_val; record (IA,IB) on tie/new max
 *   IA, IB   : indices of this pair within the original Python lists
 *
 * Notes
 * -----
 * - ‘contiguous’ fast path is used when inner strides are 1 (tight row-major),
 *   letting us advance pointers with ++.
 * - by0/by1/bx0/bx1 clamp B’s indices to the part that actually overlaps A,
 *   so no out-of-bounds reads when B sticks out of A near the borders.
 * - Equality test ignores zeros: (a && b && a==b).
 * ---------------------------------------------------------------------- */

static inline void loop_rot0_mode(
    const unsigned char* A, npy_intp Ha, npy_intp Wa, npy_intp As0, npy_intp As1,
    const unsigned char* B, npy_intp Hb, npy_intp Wb, npy_intp Bs0, npy_intp Bs1,
    long long* hist, npy_intp hist_len,
    int32_t* out, npy_intp Ho, npy_intp Wo,
    const int DO_HIST, const int DO_FULL,
    const int DO_WORST, Py_ssize_t IA, Py_ssize_t IB, worst_tracker_t* WT)
{
    /* fast-path flag: both arrays are row-major contiguous (1 byte per col step) */
    const int contiguous = (As1==1) & (Bs1==1);

    for (npy_intp oy = 0; oy < Ho; ++oy) {
        /* vertical overlap in B for this output row
           by0/by1 are B's row indices that actually land on A */
        const npy_intp by0 = (Hb-1) - oy < 0 ? 0 : (Hb-1) - oy;
        const npy_intp by1 = (Ha+Hb-2 - oy) > (Hb-1) ? (Hb-1) : (Ha+Hb-2 - oy);

        for (npy_intp ox = 0; ox < Wo; ++ox) {
            /* horizontal overlap in B for this output col */
            const npy_intp bx0 = (Wb-1) - ox < 0 ? 0 : (Wb-1) - ox;
            const npy_intp bx1 = (Wa+Wb-2 - ox) > (Wb-1) ? (Wb-1) : (Wa+Wb-2 - ox);

            int acc = 0;  /* match counter for this (oy,ox) */

            if (by1 >= by0 && bx1 >= bx0) {  /* there is some overlap */
                if (contiguous) {
                    /* contiguous: pointer-walk both rows */
                    for (npy_intp by = by0; by <= by1; ++by) {
                        /* A row that aligns with B row 'by' at output row oy */
                        const npy_intp ay = oy - (Hb-1) + by;

                        /* base pointers to start of the overlapping span */
                        const unsigned char* Ap = A + ay*As0 + (ox - (Wb-1) + bx0);
                        const unsigned char* Bp = B + by*Bs0 + bx0;

                        for (npy_intp bx = bx0; bx <= bx1; ++bx) {
                            unsigned char a = *Ap++;   /* advance along A row */
                            unsigned char b = *Bp++;   /* advance along B row */
                            if (a && b && a==b) ++acc; /* count equal nonzeros */
                        }
                    }
                } else {
                    /* generic-strides: compute each (ay,ax) with strides */
                    for (npy_intp by = by0; by <= by1; ++by) {
                        const npy_intp ay = oy - (Hb-1) + by;
                        const unsigned char* Arow = A + ay*As0;
                        const unsigned char* Brow = B + by*Bs0;

                        for (npy_intp bx = bx0; bx <= bx1; ++bx) {
                            const npy_intp ax = ox - (Wb-1) + bx;

                            unsigned char a = *(Arow + ax*As1);
                            unsigned char b = *(Brow + bx*Bs1);
                            if (a && b && a==b) ++acc;
                        }
                    }
                }
            }

            /* optional: update global "worst" (max acc) pair set */
            if (DO_WORST) {
                if (acc > WT->max_val) {
                    if (worst_reset(WT, acc) < 0) { /* ignore errors in hot path */ }
                    if (worst_add_if_new(WT, IA, IB) < 0) { }
                } else if (acc == WT->max_val) {
                    if (worst_add_if_new(WT, IA, IB) < 0) { }
                }
            }

            /* optional: bump histogram bin (clamp to valid range) */
            if (DO_HIST) {
                int bin = acc;
                if (bin < 0) bin = 0;
                if (bin >= hist_len) bin = (int)(hist_len - 1);
                hist[bin] += 1;
            }

            /* optional: write per-offset result to output map */
            if (DO_FULL) out[oy*Wo + ox] = acc;
        }
    }
}


/* Rotation convention (clockwise)
 * -------------------------------
 * We rotate B clockwise by r ∈ {0°, 90°, 180°, 270°} and slide it over A.
 * Index remapping for B’s logical coordinates (by, bx) into its memory:
 *   r = 0°   : B[ by,            bx            ]
 *   r = 90°  : B[ Hb - 1 - bx,   by            ]   // quarter turn CW
 *   r = 180° : B[ Hb - 1 - by,   Wb - 1 - bx   ]   // upside down
 *   r = 270° : B[ bx,            Wb - 1 - by   ]   // three quarters CW
 * Notes:
 * - “Clockwise” matches typical image coordinates (row = y downward, col = x right).
 * - The output map size depends on the rotation:
 *     0°/180°  → (Ha + Hb - 1) × (Wa + Wb - 1)
 *     90°/270° → (Ha + Wb - 1) × (Wa + Hb - 1)
 */

/* 180°: uses B[Hb-1-by, Wb-1-bx] */
static inline void loop_rot180_mode(
    const unsigned char* A, npy_intp Ha, npy_intp Wa, npy_intp As0, npy_intp As1,
    const unsigned char* B, npy_intp Hb, npy_intp Wb, npy_intp Bs0, npy_intp Bs1,
    long long* hist, npy_intp hist_len,
    int32_t* out, npy_intp Ho, npy_intp Wo,
    const int DO_HIST, const int DO_FULL,
    const int DO_WORST, Py_ssize_t IA, Py_ssize_t IB, worst_tracker_t* WT)
{
    const int contiguous = (As1==1) & (Bs1==1);
    for (npy_intp oy=0; oy<Ho; ++oy) {
        const npy_intp by0 = (Hb-1) - oy < 0 ? 0 : (Hb-1) - oy;
        const npy_intp by1 = (Ha+Hb-2 - oy) > (Hb-1) ? (Hb-1) : (Ha+Hb-2 - oy);
        for (npy_intp ox=0; ox<Wo; ++ox) {
            const npy_intp bx0 = (Wb-1) - ox < 0 ? 0 : (Wb-1) - ox;
            const npy_intp bx1 = (Wa+Wb-2 - ox) > (Wb-1) ? (Wb-1) : (Wa+Wb-2 - ox);
            int acc = 0;
            if (by1 >= by0 && bx1 >= bx0) {
                if (contiguous) {
                    for (npy_intp by=by0; by<=by1; ++by) {
                        const npy_intp ay = oy - (Hb-1) + by;
                        const unsigned char* Ap = A + ay*As0 + (ox - (Wb-1) + bx0);
                        const unsigned char* Bp = B + (Hb-1-by)*Bs0 + (Wb-1-bx0);
                        for (npy_intp bx=bx0; bx<=bx1; ++bx) {
                            unsigned char a = *Ap++;
                            unsigned char b = *Bp--;
                            if (a && b && a==b) ++acc;
                        }
                    }
                } else {
                    for (npy_intp by=by0; by<=by1; ++by) {
                        const npy_intp ay = oy - (Hb-1) + by;
                        const unsigned char* Arow = A + ay*As0;
                        const unsigned char* Brow = B + (Hb-1-by)*Bs0;
                        for (npy_intp bx=bx0; bx<=bx1; ++bx) {
                            const npy_intp ax = ox - (Wb-1) + bx;
                            unsigned char a = *(Arow + ax*As1);
                            unsigned char b = *(Brow + (Wb-1-bx)*Bs1);
                            if (a && b && a==b) ++acc;
                        }
                    }
                }
            }
            if (DO_WORST) {
                if (acc > WT->max_val) {
                    if (worst_reset(WT, acc) < 0) { }
                    if (worst_add_if_new(WT, IA, IB) < 0) { }
                } else if (acc == WT->max_val) {
                    if (worst_add_if_new(WT, IA, IB) < 0) { }
                }
            }
            if (DO_HIST) {
                int bin = acc;
                if (bin < 0) bin = 0;
                if (bin >= hist_len) bin = (int)(hist_len - 1);
                hist[bin] += 1;
            }
            if (DO_FULL) out[oy*Wo + ox] = acc;
        }
    }
}

/* 90°: uses B[Hb-1-bx, by]  (clockwise quarter-turn) */
static inline void loop_rot90_mode(
    const unsigned char* A, npy_intp Ha, npy_intp Wa, npy_intp As0, npy_intp As1,
    const unsigned char* B, npy_intp Hb, npy_intp Wb, npy_intp Bs0, npy_intp Bs1,
    long long* hist, npy_intp hist_len,
    int32_t* out, npy_intp Ho, npy_intp Wo,
    const int DO_HIST, const int DO_FULL,
    const int DO_WORST, Py_ssize_t IA, Py_ssize_t IB, worst_tracker_t* WT)
{
    const int contiguous = (As1==1) & (Bs1==1);
    for (npy_intp oy=0; oy<Ho; ++oy) {
        const npy_intp by0r = (Wb-1) - oy < 0 ? 0 : (Wb-1) - oy;
        const npy_intp by1r = (Ha+Wb-2 - oy) > (Wb-1) ? (Wb-1) : (Ha+Wb-2 - oy);
        for (npy_intp ox=0; ox<Wo; ++ox) {
            const npy_intp bx0r = (Hb-1) - ox < 0 ? 0 : (Hb-1) - ox;
            const npy_intp bx1r = (Wa+Hb-2 - ox) > (Hb-1) ? (Hb-1) : (Wa+Hb-2 - ox);
            int acc = 0;
            if (by1r >= by0r && bx1r >= bx0r) {
                if (contiguous) {
                    for (npy_intp by_r=by0r; by_r<=by1r; ++by_r) {
                        const npy_intp ay = oy - (Wb-1) + by_r;
                        const unsigned char* Ap = A + ay*As0 + (ox - (Hb-1) + bx0r);
                        for (npy_intp bx_r=bx0r; bx_r<=bx1r; ++bx_r) {
                            const unsigned char* Brow = B + (Hb-1-bx_r)*Bs0;
                            unsigned char a = *Ap++;
                            unsigned char b = *(Brow + by_r*Bs1);
                            if (a && b && a==b) ++acc;
                        }
                    }
                } else {
                    for (npy_intp by_r=by0r; by_r<=by1r; ++by_r) {
                        const npy_intp ay = oy - (Wb-1) + by_r;
                        const unsigned char* Arow = A + ay*As0;
                        for (npy_intp bx_r=bx0r; bx_r<=bx1r; ++bx_r) {
                            const npy_intp ax = ox - (Hb-1) + bx_r;
                            const unsigned char* Brow = B + (Hb-1-bx_r)*Bs0;
                            unsigned char a = *(Arow + ax*As1);
                            unsigned char b = *(Brow + by_r*Bs1);
                            if (a && b && a==b) ++acc;
                        }
                    }
                }
            }
            if (DO_WORST) {
                if (acc > WT->max_val) {
                    if (worst_reset(WT, acc) < 0) { }
                    if (worst_add_if_new(WT, IA, IB) < 0) { }
                } else if (acc == WT->max_val) {
                    if (worst_add_if_new(WT, IA, IB) < 0) { }
                }
            }
            if (DO_HIST) {
                int bin = acc;
                if (bin < 0) bin = 0;
                if (bin >= hist_len) bin = (int)(hist_len - 1);
                hist[bin] += 1;
            }
            if (DO_FULL) out[oy*Wo + ox] = acc;
        }
    }
}

/* 270°: uses B[bx, Wb-1-by]  (clockwise three-quarter turn) */
static inline void loop_rot270_mode(
    const unsigned char* A, npy_intp Ha, npy_intp Wa, npy_intp As0, npy_intp As1,
    const unsigned char* B, npy_intp Hb, npy_intp Wb, npy_intp Bs0, npy_intp Bs1,
    long long* hist, npy_intp hist_len,
    int32_t* out, npy_intp Ho, npy_intp Wo,
    const int DO_HIST, const int DO_FULL,
    const int DO_WORST, Py_ssize_t IA, Py_ssize_t IB, worst_tracker_t* WT)
{
    const int contiguous = (As1==1) & (Bs1==1);
    for (npy_intp oy=0; oy<Ho; ++oy) {
        const npy_intp by0r = (Wb-1) - oy < 0 ? 0 : (Wb-1) - oy;
        const npy_intp by1r = (Ha+Wb-2 - oy) > (Wb-1) ? (Wb-1) : (Ha+Wb-2 - oy);
        for (npy_intp ox=0; ox<Wo; ++ox) {
            const npy_intp bx0r = (Hb-1) - ox < 0 ? 0 : (Hb-1) - ox;
            const npy_intp bx1r = (Wa+Hb-2 - ox) > (Hb-1) ? (Hb-1) : (Wa+Hb-2 - ox);
            int acc = 0;
            if (by1r >= by0r && bx1r >= bx0r) {
                if (contiguous) {
                    for (npy_intp by_r=by0r; by_r<=by1r; ++by_r) {
                        const npy_intp ay = oy - (Wb-1) + by_r;
                        const unsigned char* Ap = A + ay*As0 + (ox - (Hb-1) + bx0r);
                        for (npy_intp bx_r=bx0r; bx_r<=bx1r; ++bx_r) {
                            const unsigned char* Brow = B + bx_r*Bs0;
                            unsigned char a = *Ap++;
                            unsigned char b = *(Brow + (Wb-1-by_r)*Bs1);
                            if (a && b && a==b) ++acc;
                        }
                    }
                } else {
                    for (npy_intp by_r=by0r; by_r<=by1r; ++by_r) {
                        const npy_intp ay = oy - (Wb-1) + by_r;
                        const unsigned char* Arow = A + ay*As0;
                        for (npy_intp bx_r=bx0r; bx_r<=bx1r; ++bx_r) {
                            const npy_intp ax = ox - (Hb-1) + bx_r;
                            const unsigned char* Brow = B + bx_r*Bs0;
                            unsigned char a = *(Arow + ax*As1);
                            unsigned char b = *(Brow + (Wb-1-by_r)*Bs1);
                            if (a && b && a==b) ++acc;
                        }
                    }
                }
            }
            if (DO_WORST) {
                if (acc > WT->max_val) {
                    if (worst_reset(WT, acc) < 0) { }
                    if (worst_add_if_new(WT, IA, IB) < 0) { }
                } else if (acc == WT->max_val) {
                    if (worst_add_if_new(WT, IA, IB) < 0) { }
                }
            }
            if (DO_HIST) {
                int bin = acc;
                if (bin < 0) bin = 0;
                if (bin >= hist_len) bin = (int)(hist_len - 1);
                hist[bin] += 1;
            }
            if (DO_FULL) out[oy*Wo + ox] = acc;
        }
    }
}

/* Generate 3 wrappers (hist-only, full-only, both) for a given base NAME.
 * Each wrapper sets compile-time constants (DO_HIST/DO_FULL) and passes
 * either a real pointer or NULL for hist/out to avoid inner-branching.
 */
#define DECL_WRAP(NAME) \
static inline void NAME##_hist( \
    const unsigned char* A, npy_intp Ha, npy_intp Wa, npy_intp As0, npy_intp As1, \
    const unsigned char* B, npy_intp Hb, npy_intp Wb, npy_intp Bs0, npy_intp Bs1, \
    long long* hist, npy_intp hist_len, int32_t* out, npy_intp Ho, npy_intp Wo, \
    const int DO_WORST, Py_ssize_t IA, Py_ssize_t IB, worst_tracker_t* WT) { \
    /* DO_HIST=1, DO_FULL=0; pass out=NULL */ \
    NAME##_mode(A,Ha,Wa,As0,As1, B,Hb,Wb,Bs0,Bs1, \
                hist, hist_len, NULL, Ho,Wo, \
                1, 0, DO_WORST, IA,IB, WT); } \
static inline void NAME##_full( \
    const unsigned char* A, npy_intp Ha, npy_intp Wa, npy_intp As0, npy_intp As1, \
    const unsigned char* B, npy_intp Hb, npy_intp Wb, npy_intp Bs0, npy_intp Bs1, \
    long long* hist, npy_intp hist_len, int32_t* out, npy_intp Ho, npy_intp Wo, \
    const int DO_WORST, Py_ssize_t IA, Py_ssize_t IB, worst_tracker_t* WT) { \
    /* DO_HIST=0, DO_FULL=1; pass hist=NULL */ \
    NAME##_mode(A,Ha,Wa,As0,As1, B,Hb,Wb,Bs0,Bs1, \
                NULL, 0, out, Ho,Wo, \
                0, 1, DO_WORST, IA,IB, WT); } \
static inline void NAME##_both( \
    const unsigned char* A, npy_intp Ha, npy_intp Wa, npy_intp As0, npy_intp As1, \
    const unsigned char* B, npy_intp Hb, npy_intp Wb, npy_intp Bs0, npy_intp Bs1, \
    long long* hist, npy_intp hist_len, int32_t* out, npy_intp Ho, npy_intp Wo, \
    const int DO_WORST, Py_ssize_t IA, Py_ssize_t IB, worst_tracker_t* WT) { \
    /* DO_HIST=1, DO_FULL=1; pass both pointers */ \
    NAME##_mode(A,Ha,Wa,As0,As1, B,Hb,Wb,Bs0,Bs1, \
                hist, hist_len, out, Ho,Wo, \
                1, 1, DO_WORST, IA,IB, WT); }

/* Instantiate for all four rotations. */
DECL_WRAP(loop_rot0)
DECL_WRAP(loop_rot90)
DECL_WRAP(loop_rot180)
DECL_WRAP(loop_rot270)

#undef DECL_WRAP




/* ------------------ main API (unchanged externally except extra flag & return item) ------------------ */

/* -------------------------------------------------------------------------
 * eqcorr2d_compute
 *
 * Python entry point: eqcorr2d.compute(
 *     A_list, B_list, rot0, rot90, rot180, rot270, do_hist, do_full, report_worst
 * )
 * Returns a 6-tuple:
 *   (hist_or_None, outs0_or_None, outs90_or_None, outs180_or_None, outs270_or_None,
 *    worst_pairs_or_None)
 * ------------------------------------------------------------------------- */
static PyObject* eqcorr2d_compute(PyObject* self, PyObject* args)
{
    PyObject *seqA_obj, *seqB_obj;
    int f0, f90, f180, f270, do_hist, do_full, do_worst;

    /* Parse Python args; final 'p' (bool) is our report_worst flag. */
    if (!PyArg_ParseTuple(args, "OOppppppp",
                          &seqA_obj, &seqB_obj,
                          &f0, &f90, &f180, &f270,
                          &do_hist, &do_full, &do_worst)) {
        return NULL;
    }

#ifdef _OPENMP
    /* We run under Python multiprocessing; keep OpenMP at 1 thread to avoid oversubscription. */
    omp_set_num_threads(1);
#endif

    /* Convert A_list/B_list to fast sequence form; no copying of array data here. */
    PyObject *A_fast = PySequence_Fast(seqA_obj, "A_list must be a sequence");
    if (!A_fast) return NULL;
    PyObject *B_fast = PySequence_Fast(seqB_obj, "B_list must be a sequence");
    if (!B_fast) { Py_DECREF(A_fast); return NULL; }

    /* nA/nB = number of arrays in each list. A_items/B_items are raw pointers to elements. */
    Py_ssize_t nA = PySequence_Fast_GET_SIZE(A_fast);
    Py_ssize_t nB = PySequence_Fast_GET_SIZE(B_fast);
    PyObject **A_items = PySequence_Fast_ITEMS(A_fast);
    PyObject **B_items = PySequence_Fast_ITEMS(B_fast);

    /* -------------------- Optional histogram setup --------------------
     * Histogram length = max(Hb*Wb) + 1 across all B’s.
     * Index k in the histogram counts “how many offsets produced exactly k matches”.
     */
    npy_intp max_prod = 0;
    for (Py_ssize_t j=0; j<nB; ++j) {
        PyArrayObject* B = (PyArrayObject*)B_items[j];  /* NumPy array (uint8, 2D) */
        npy_intp Hb = PyArray_DIM(B,0), Wb = PyArray_DIM(B,1);
        npy_intp prod = Hb * Wb;
        if (prod > max_prod) max_prod = prod;
    }
    if (max_prod < 1) max_prod = 1;
    npy_intp hdim = max_prod + 1;

    PyArrayObject* Hist = NULL;   /* the NumPy array we’ll return as hist */
    long long* hist = NULL;       /* raw pointer to its data for fast increments */
    if (do_hist) {
        Hist = (PyArrayObject*)PyArray_Zeros(1, &hdim, PyArray_DescrFromType(NPY_INT64), 0);
        if (!Hist) { Py_DECREF(A_fast); Py_DECREF(B_fast); return NULL; }
        hist = (long long*)PyArray_DATA(Hist);
    }

    /* -------------------- Optional “worst” (max) tracker --------------------
     * If enabled, we track the largest match count seen so far (WT->max_val)
     * and store unique (iA, iB) pairs that reached that max (WT->pairs).
     * WT->seen is an nA*nB bitmap to avoid duplicate (iA,iB) entries.
     */
    worst_tracker_t WT_local;
    worst_tracker_t* WT = NULL;
    if (do_worst) {
        WT = &WT_local;
        WT->max_val = INT_MIN;             /* so first real value wins */
        WT->nA = nA; WT->nB = nB;          /* dimensions for the seen bitmap */
        WT->pairs = PyList_New(0);         /* list of (iA, iB) tuples for the return */
        if (!WT->pairs) { Py_DECREF(A_fast); Py_DECREF(B_fast); Py_XDECREF(Hist); return NULL; }
        WT->seen = (unsigned char*)calloc((size_t)(nA * nB), 1);
        if (!WT->seen) { Py_DECREF(A_fast); Py_DECREF(B_fast); Py_XDECREF(Hist); Py_DECREF(WT->pairs); return PyErr_NoMemory(); }
    }

    /* -------------------- Optional full per-pair outputs --------------------
     * If do_full: for each requested rotation, build a [nA][nB] nested list.
     * Each cell will hold a 2D int32 NumPy array with the correlation map.
     * If do_full==0: we return None for that rotation.
     */
    PyObject *L0 = Py_None, *L90 = Py_None, *L180 = Py_None, *L270 = Py_None;
    if (do_full) {
        if (f0)   { L0   = PyList_New(nA); if (!L0)   goto fail; }
        if (f90)  { L90  = PyList_New(nA); if (!L90)  goto fail; }
        if (f180) { L180 = PyList_New(nA); if (!L180) goto fail; }
        if (f270) { L270 = PyList_New(nA); if (!L270) goto fail; }
        /* Pre-create inner rows [nB] so later we can set [i][j] directly. */
        for (Py_ssize_t i=0; i<nA; ++i) {
            if (f0)   { PyObject* row = PyList_New(nB); if (!row) goto fail; PyList_SET_ITEM(L0,   i, row); }
            if (f90)  { PyObject* row = PyList_New(nB); if (!row) goto fail; PyList_SET_ITEM(L90,  i, row); }
            if (f180) { PyObject* row = PyList_New(nB); if (!row) goto fail; PyList_SET_ITEM(L180, i, row); }
            if (f270) { PyObject* row = PyList_New(nB); if (!row) goto fail; PyList_SET_ITEM(L270, i, row); }
        }
    } else {
        /* Match API: put Py_None in return tuple for rotations we’re not materializing. */
        Py_INCREF(Py_None); L0 = Py_None;
        Py_INCREF(Py_None); L90 = Py_None;
        Py_INCREF(Py_None); L180 = Py_None;
        Py_INCREF(Py_None); L270 = Py_None;
    }

    /* -------------------- Core: iterate over all (A_i, B_j) pairs -------------------- */
    for (Py_ssize_t i=0; i<nA; ++i) {
        /* Borrow raw pointers, sizes, and strides from A_i (already NumPy arrays). */
        PyArrayObject* A = (PyArrayObject*)A_items[i];
        const unsigned char* Ad = (const unsigned char*)PyArray_DATA(A);
        const npy_intp Ha = PyArray_DIM(A,0), Wa = PyArray_DIM(A,1);
        const npy_intp As0 = PyArray_STRIDES(A)[0], As1 = PyArray_STRIDES(A)[1];

        for (Py_ssize_t j=0; j<nB; ++j) {
            PyArrayObject* B = (PyArrayObject*)B_items[j];
            const unsigned char* Bd = (const unsigned char*)PyArray_DATA(B);
            const npy_intp Hb = PyArray_DIM(B,0), Wb = PyArray_DIM(B,1);
            const npy_intp Bs0 = PyArray_STRIDES(B)[0], Bs1 = PyArray_STRIDES(B)[1];

            /* ---- 0° rotation ---- */
            if (f0) {
                const npy_intp Ho = Ha + Hb - 1, Wo = Wa + Wb - 1;
                int32_t* out = NULL; PyArrayObject* O = NULL;
                if (do_full) {
                    npy_intp dims[2] = {Ho, Wo};
                    O = (PyArrayObject*)PyArray_SimpleNew(2, dims, NPY_INT32);
                    if (!O) goto fail;
                    out = (int32_t*)PyArray_DATA(O);
                }
                if (do_hist && !do_full)
                    loop_rot0_hist(Ad,Ha,Wa,As0,As1, Bd,Hb,Wb,Bs0,Bs1, hist, hdim, NULL, Ho, Wo,
                                   do_worst, i, j, WT);
                else if (!do_hist && do_full)
                    loop_rot0_full(Ad,Ha,Wa,As0,As1, Bd,Hb,Wb,Bs0,Bs1, NULL, 0, out, Ho, Wo,
                                   do_worst, i, j, WT);
                else
                    loop_rot0_both(Ad,Ha,Wa,As0,As1, Bd,Hb,Wb,Bs0,Bs1, hist, hdim, out, Ho, Wo,
                                   do_worst, i, j, WT);
                if (do_full) { PyList_SET_ITEM(PyList_GET_ITEM(L0,i), j, (PyObject*)O); }
            }

            /* ---- 90° rotation ---- */
            if (f90) {
                const npy_intp Ho = Ha + Wb - 1, Wo = Wa + Hb - 1;
                int32_t* out = NULL; PyArrayObject* O = NULL;
                if (do_full) {
                    npy_intp dims[2] = {Ho, Wo};
                    O = (PyArrayObject*)PyArray_SimpleNew(2, dims, NPY_INT32);
                    if (!O) goto fail;
                    out = (int32_t*)PyArray_DATA(O);
                }
                if (do_hist && !do_full)
                    loop_rot90_hist(Ad,Ha,Wa,As0,As1, Bd,Hb,Wb,Bs0,Bs1, hist, hdim, NULL, Ho, Wo,
                                    do_worst, i, j, WT);
                else if (!do_hist && do_full)
                    loop_rot90_full(Ad,Ha,Wa,As0,As1, Bd,Hb,Wb,Bs0,Bs1, NULL, 0, out, Ho, Wo,
                                    do_worst, i, j, WT);
                else
                    loop_rot90_both(Ad,Ha,Wa,As0,As1, Bd,Hb,Wb,Bs0,Bs1, hist, hdim, out, Ho, Wo,
                                    do_worst, i, j, WT);
                if (do_full) { PyList_SET_ITEM(PyList_GET_ITEM(L90,i), j, (PyObject*)O); }
            }

            /* ---- 180° rotation ---- */
            if (f180) {
                const npy_intp Ho = Ha + Hb - 1, Wo = Wa + Wb - 1;
                int32_t* out = NULL; PyArrayObject* O = NULL;
                if (do_full) {
                    npy_intp dims[2] = {Ho, Wo};
                    O = (PyArrayObject*)PyArray_SimpleNew(2, dims, NPY_INT32);
                    if (!O) goto fail;
                    out = (int32_t*)PyArray_DATA(O);
                }
                if (do_hist && !do_full)
                    loop_rot180_hist(Ad,Ha,Wa,As0,As1, Bd,Hb,Wb,Bs0,Bs1, hist, hdim, NULL, Ho, Wo,
                                     do_worst, i, j, WT);
                else if (!do_hist && do_full)
                    loop_rot180_full(Ad,Ha,Wa,As0,As1, Bd,Hb,Wb,Bs0,Bs1, NULL, 0, out, Ho, Wo,
                                     do_worst, i, j, WT);
                else
                    loop_rot180_both(Ad,Ha,Wa,As0,As1, Bd,Hb,Wb,Bs0,Bs1, hist, hdim, out, Ho, Wo,
                                     do_worst, i, j, WT);
                if (do_full) { PyList_SET_ITEM(PyList_GET_ITEM(L180,i), j, (PyObject*)O); }
            }

            /* ---- 270° rotation ---- */
            if (f270) {
                const npy_intp Ho = Ha + Wb - 1, Wo = Wa + Hb - 1;
                int32_t* out = NULL; PyArrayObject* O = NULL;
                if (do_full) {
                    npy_intp dims[2] = {Ho, Wo};
                    O = (PyArrayObject*)PyArray_SimpleNew(2, dims, NPY_INT32);
                    if (!O) goto fail;
                    out = (int32_t*)PyArray_DATA(O);
                }
                if (do_hist && !do_full)
                    loop_rot270_hist(Ad,Ha,Wa,As0,As1, Bd,Hb,Wb,Bs0,Bs1, hist, hdim, NULL, Ho, Wo,
                                     do_worst, i, j, WT);
                else if (!do_hist && do_full)
                    loop_rot270_full(Ad,Ha,Wa,As0,As1, Bd,Hb,Wb,Bs0,Bs1, NULL, 0, out, Ho, Wo,
                                     do_worst, i, j, WT);
                else
                    loop_rot270_both(Ad,Ha,Wa,As0,As1, Bd,Hb,Wb,Bs0,Bs1, hist, hdim, out, Ho, Wo,
                                     do_worst, i, j, WT);
                if (do_full) { PyList_SET_ITEM(PyList_GET_ITEM(L270,i), j, (PyObject*)O); }
            }
        }
    }

    /* We’re done reading A_list/B_list. */
    Py_DECREF(A_fast);
    Py_DECREF(B_fast);

    /* -------------------- Build Python return tuple -------------------- */
    {
        PyObject* ret = PyTuple_New(6);
        /* slot 0: histogram or None */
        if (do_hist) PyTuple_SET_ITEM(ret, 0, (PyObject*)Hist);
        else         { Py_INCREF(Py_None); PyTuple_SET_ITEM(ret, 0, Py_None); }

        /* slots 1..4: per-rotation outputs or None (set above) */
        PyTuple_SET_ITEM(ret, 1, L0);
        PyTuple_SET_ITEM(ret, 2, L90);
        PyTuple_SET_ITEM(ret, 3, L180);
        PyTuple_SET_ITEM(ret, 4, L270);

        /* slot 5: worst pairs or None; free bitmap if we used it */
        if (do_worst) {
            PyTuple_SET_ITEM(ret, 5, WT->pairs);  /* transfer ownership of list to Python */
            free(WT->seen);
        } else {
            Py_INCREF(Py_None);
            PyTuple_SET_ITEM(ret, 5, Py_None);
        }
        return ret;
    }

/* Any allocation error jumps here; clean up what we own and return NULL. */
fail:
    if (do_worst) {
        if (WT->pairs) Py_DECREF(WT->pairs);
        if (WT->seen) free(WT->seen);
    }
    Py_XDECREF(Hist);
    if (do_full) { Py_XDECREF(L0); Py_XDECREF(L90); Py_XDECREF(L180); Py_XDECREF(L270); }
    Py_DECREF(A_fast);
    Py_DECREF(B_fast);
    return NULL;
}

/* -------------------- Python module glue -------------------- */
static PyMethodDef methods[] = {
    /* One public symbol: compute(...) -> 6-tuple described above */
    {"compute", (PyCFunction)eqcorr2d_compute, METH_VARARGS,
     "compute(A_list, B_list, rot0, rot90, rot180, rot270, do_hist, do_full, report_worst)\n"
     "Return (hist, outs0, outs90, outs180, outs270, worst_pairs_or_None). "
     "If do_full, outs* is [nA][nB] of int32 maps. Inputs are 2D uint8; zeros ignored."},
    {NULL,NULL,0,NULL}
};

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT, "eqcorr2d",
    "Equality-correlation with rotations (zeros ignored).",
    -1, methods
};

PyMODINIT_FUNC PyInit_eqcorr2d(void) {
    import_array();                 /* required by NumPy C-API */
    return PyModule_Create(&moduledef);
}
