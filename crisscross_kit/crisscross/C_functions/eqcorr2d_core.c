#include "eqcorr2d.h"

/* ---- worst_tracker_t helpers -------------------------------------------------
 * Purpose: Manage the set of (iA, iB) pairs that achieved the CURRENT global
 * maximum match value during a run. When a strictly larger maximum is found,
 * we reset the tracker (clear bitmap + empty Python list). When we encounter
 * another offset that ties the current maximum, we add the pair if not yet
 * recorded (using a flattened nA*nB bitmap to avoid duplicates).
 *
 * Lifetime notes:
 * - The worst_tracker_t struct itself typically lives on the stack.
 * - The 'seen' bitmap is calloc'd by the binding and free'd there after use.
 * - The 'pairs' list is created in the binding; ownership is transferred to
 *   the Python return tuple (refcounting handled in the binding).
 * --------------------------------------------------------------------------- */
int worst_reset(worst_tracker_t* wt, int new_max) {
    wt->max_val = new_max;
    if (wt->seen) memset(wt->seen, 0, (size_t)(wt->nA * wt->nB));
    if (!wt->pairs) return 0;
    if (PyList_SetSlice(wt->pairs, 0, PyList_GET_SIZE(wt->pairs), NULL) < 0) return -1;
    return 0;
}

// Update: use npy_intp for indices to match header
int worst_add_if_new(worst_tracker_t* wt, npy_intp ia, npy_intp ib) {
    if (!wt->pairs || !wt->seen) return 0;
    npy_intp idx = ia * wt->nB + ib;
    if (wt->seen[idx]) return 0;
    wt->seen[idx] = 1;
    PyObject* tup = Py_BuildValue("(nn)", ia, ib);
    if (!tup) return -1;
    int rc = PyList_Append(wt->pairs, tup);
    Py_DECREF(tup);
    return rc;
}

// The four tight-loop kernels are taken from the original eqcorr2d.c, with identical behavior.

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

/* ----------------------------------------------------------------------
 * loop_rot0_mode — one A–B pair at 0° rotation
 *
 * What it does
 * ------------
 * Slides B over A at every offset (ox, oy). For each overlap window,
 * counts matches of equal, non-zero entries (acc). Optionally:
 *   - adds acc to a global histogram,
 *   - writes acc into the full 2D output map,
 *   - updates a global “worst” tracker (max acc seen; stores (IA,IB) pairs).
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
void loop_rot0_mode(
    const u8* EQ_RESTRICT A, npy_intp Ha, npy_intp Wa, npy_intp As0, npy_intp As1,
    const u8* EQ_RESTRICT B, npy_intp Hb, npy_intp Wb, npy_intp Bs0, npy_intp Bs1,
    hist_t* EQ_RESTRICT hist, npy_intp hist_len,
    out_t* EQ_RESTRICT out, npy_intp Ho, npy_intp Wo,
    int DO_HIST, int DO_FULL,
    int DO_WORST, npy_intp IA, npy_intp IB, worst_tracker_t* WT)
{
    const int contiguous = (As1==1) & (Bs1==1);
    for (npy_intp oy = 0; oy < Ho; ++oy) {
        const npy_intp by0 = (Hb-1) - oy < 0 ? 0 : (Hb-1) - oy;
        const npy_intp by1 = (Ha+Hb-2 - oy) > (Hb-1) ? (Hb-1) : (Ha+Hb-2 - oy);
        for (npy_intp ox = 0; ox < Wo; ++ox) {
            const npy_intp bx0 = (Wb-1) - ox < 0 ? 0 : (Wb-1) - ox;
            const npy_intp bx1 = (Wa+Wb-2 - ox) > (Wb-1) ? (Wb-1) : (Wa+Wb-2 - ox);
            int acc = 0;
            if (by1 >= by0 && bx1 >= bx0) {
                if (contiguous) {
                    for (npy_intp by = by0; by <= by1; ++by) {
                        const npy_intp ay = oy - (Hb-1) + by;
                        const u8* Ap = A + ay*As0 + (ox - (Wb-1) + bx0);
                        const u8* Bp = B + by*Bs0 + bx0;
                        for (npy_intp bx = bx0; bx <= bx1; ++bx) {
                            u8 a = *Ap++;
                            u8 b = *Bp++;
                            if (a && b && a==b) ++acc;
                        }
                    }
                } else {
                    for (npy_intp by = by0; by <= by1; ++by) {
                        const npy_intp ay = oy - (Hb-1) + by;
                        const u8* Arow = A + ay*As0;
                        const u8* Brow = B + by*Bs0;
                        for (npy_intp bx = bx0; bx <= bx1; ++bx) {
                            const npy_intp ax = ox - (Wb-1) + bx;
                            u8 a = *(Arow + ax*As1);
                            u8 b = *(Brow + bx*Bs1);
                            if (a && b && a==b) ++acc;
                        }
                    }
                }
            }
            if (DO_WORST) {
                if (acc > WT->max_val) {
                    if (worst_reset(WT, acc) < 0) {}
                    if (worst_add_if_new(WT, IA, IB) < 0) {}
                } else if (acc == WT->max_val) {
                    if (worst_add_if_new(WT, IA, IB) < 0) {}
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
