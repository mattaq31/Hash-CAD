#ifndef EQCORR2D_H
#define EQCORR2D_H

// Shared declarations for the eqcorr2d module.
// Purpose
// -------
// Centralize lightweight data structures and function prototypes that are used
// by both the tight C kernels (core) and the Python bindings.

#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <numpy/arrayobject.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// Portable restrict macro to enable better optimization when supported by
// the compiler. Expands to nothing on compilers that don't support it.
#ifndef EQ_RESTRICT
# if defined(__STDC_VERSION__) && __STDC_VERSION__ >= 199901L
#  define EQ_RESTRICT restrict
# elif defined(__GNUC__) || defined(__clang__)
#  define EQ_RESTRICT __restrict__
# elif defined(_MSC_VER)
#  define EQ_RESTRICT __restrict
# else
#  define EQ_RESTRICT
# endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

// Small helpful typedefs for readability and easy tuning
typedef unsigned char u8;
typedef int32_t out_t;   // per-offset output element type
typedef long long hist_t; // histogram bin type

// Track (iA, iB) pairs achieving the global maximum match value.
typedef struct {
    int            max_val;
    npy_intp       nA, nB;         // matrix dimensions (nA rows x nB cols)
    uint32_t*      counts;         // nA*nB counter matrix; counts[ia*nB + ib]
} worst_tracker_t;

// Helpers for worst tracking (counting version)
int worst_reset(worst_tracker_t *wt, int new_max);
int worst_count(worst_tracker_t *wt, npy_intp ia, npy_intp ib);

// Core tight-loop kernel for 0° rotation mode only. All other rotations
// are handled by pre-rotating B in the binding layer.
void loop_rot0_mode(
    const u8 *EQ_RESTRICT A, npy_intp Ha, npy_intp Wa, npy_intp As0, npy_intp As1,
    const u8 *EQ_RESTRICT B, npy_intp Hb, npy_intp Wb, npy_intp Bs0, npy_intp Bs1,
    hist_t *EQ_RESTRICT hist, npy_intp hist_len,
    out_t *EQ_RESTRICT out, npy_intp Ho, npy_intp Wo,
    int DO_HIST, int DO_FULL,
    int DO_WORST, npy_intp IA, npy_intp IB, worst_tracker_t *WT);

#ifdef __cplusplus
}
#endif

#endif // EQCORR2D_H
