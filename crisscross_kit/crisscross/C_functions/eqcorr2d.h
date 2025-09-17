#ifndef EQCORR2D_H
#define EQCORR2D_H

// Shared declarations for the eqcorr2d module.
// Purpose
// -------
// Centralize lightweight data structures and function prototypes that are used
// by both the tight C kernels (core) and the Python bindings.
//
// Design notes
// ------------
// - Standard C only in this header and the core implementation. The binding is
//   the only place that touches Python/NumPy objects and reference counting.
// - We implement a "2D equality correlation" where, instead of multiply+sum as
//   in convolution, we count the number of positions that are exactly equal.
// - Zeros are treated as "don't care": (a==0 || b==0) never contributes.
// - Rotations of the small pattern B are supported at 0°, 90°, 180°, 270°.
// - Optional features controlled by the binding:
//     * Global histogram of match counts per offset
//     * Full per-pair output maps (int32) for requested rotations
//     * Tracking of the (iA, iB) pairs that achieve the global maximum match
//
// The detailed rationale, rotation convention, and algorithm overview are kept
// as rich comments alongside the corresponding function definitions in the
// implementation files to aid maintainability.

#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <numpy/arrayobject.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

#ifdef __cplusplus
extern "C" {
#endif

// Track (iA, iB) pairs achieving the global maximum match value.
typedef struct {
    int            max_val;
    Py_ssize_t     nA, nB;
    unsigned char* seen;   // bitmap size nA*nB
    PyObject*      pairs;  // Python list of (iA, iB)
} worst_tracker_t;

// Helpers for worst tracking
int worst_reset(worst_tracker_t *wt, int new_max);
int worst_add_if_new(worst_tracker_t *wt, Py_ssize_t ia, Py_ssize_t ib);

// Core tight-loop kernels for each rotation mode. These functions implement
// the sliding equality correlation with zeros ignored, and optionally:
// - update a global histogram (hist)
// - write per-offset results into out (if DO_FULL)
// - update a worst-pair tracker (if DO_WORST)
// All dimensions/strides use NumPy's npy_intp where relevant.
void loop_rot0_mode(
    const unsigned char *A, npy_intp Ha, npy_intp Wa, npy_intp As0, npy_intp As1,
    const unsigned char *B, npy_intp Hb, npy_intp Wb, npy_intp Bs0, npy_intp Bs1,
    long long *hist, npy_intp hist_len,
    int32_t *out, npy_intp Ho, npy_intp Wo,
    const int DO_HIST, const int DO_FULL,
    const int DO_WORST, Py_ssize_t IA, Py_ssize_t IB, worst_tracker_t *WT);

void loop_rot180_mode(
    const unsigned char *A, npy_intp Ha, npy_intp Wa, npy_intp As0, npy_intp As1,
    const unsigned char *B, npy_intp Hb, npy_intp Wb, npy_intp Bs0, npy_intp Bs1,
    long long *hist, npy_intp hist_len,
    int32_t *out, npy_intp Ho, npy_intp Wo,
    const int DO_HIST, const int DO_FULL,
    const int DO_WORST, Py_ssize_t IA, Py_ssize_t IB, worst_tracker_t *WT);

void loop_rot90_mode(
    const unsigned char *A, npy_intp Ha, npy_intp Wa, npy_intp As0, npy_intp As1,
    const unsigned char *B, npy_intp Hb, npy_intp Wb, npy_intp Bs0, npy_intp Bs1,
    long long *hist, npy_intp hist_len,
    int32_t *out, npy_intp Ho, npy_intp Wo,
    const int DO_HIST, const int DO_FULL,
    const int DO_WORST, Py_ssize_t IA, Py_ssize_t IB, worst_tracker_t *WT);

void loop_rot270_mode(
    const unsigned char *A, npy_intp Ha, npy_intp Wa, npy_intp As0, npy_intp As1,
    const unsigned char *B, npy_intp Hb, npy_intp Wb, npy_intp Bs0, npy_intp Bs1,
    long long *hist, npy_intp hist_len,
    int32_t *out, npy_intp Ho, npy_intp Wo,
    const int DO_HIST, const int DO_FULL,
    const int DO_WORST, Py_ssize_t IA, Py_ssize_t IB, worst_tracker_t *WT);

#ifdef __cplusplus
}
#endif

#endif // EQCORR2D_H
