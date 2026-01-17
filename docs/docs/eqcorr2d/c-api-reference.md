# C Engine API Reference

The `eqcorr2d` C engine provides high-performance computation of 2D equality correlations between handle arrays. This page documents the low-level C API exposed to Python.

!!! warning "Advanced Usage"
    Most users should use the high-level Python interface (:func:`~eqcorr2d.eqcorr2d_interface.wrap_eqcorr2d` or :func:`~eqcorr2d.eqcorr2d_interface.comprehensive_score_analysis`) instead of calling the C engine directly.

## Module: `eqcorr2d_engine`

The compiled C extension module exposes a single function: `compute`.

### `eqcorr2d_engine.compute`

```python
def compute(
    A_list: Sequence[np.ndarray],
    B_list: Sequence[np.ndarray],
    compute_instructions: np.ndarray,
    do_hist: int,
    do_full: int,
    do_worst: int,
    do_local: int = 0,
) -> Tuple[
    Optional[np.ndarray],              # Global histogram
    Optional[List[List[np.ndarray]]],  # Full match matrices
    None,                              # Deprecated (always None)
    Optional[np.ndarray],              # Local histograms (3D array)
]
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `A_list` | `Sequence[np.ndarray]` | Sequence of 2D uint8 arrays representing handle occupancy. Shape: `(H, W)` for each array. |
| `B_list` | `Sequence[np.ndarray]` | Sequence of 2D uint8 arrays representing antihandle occupancy. Same requirements as `A_list`. |
| `compute_instructions` | `np.ndarray` | 2D uint8 array of shape `(len(A_list), len(B_list))`. Entry `[i,j]==1` means compute pair `(A[i], B[j])`; `0` means skip. |
| `do_hist` | `int` | If 1, accumulate a global histogram of match counts. |
| `do_full` | `int` | If 1, return full 2D result maps for every computed pair. |
| `do_worst` | `int` | **Deprecated.** Always pass 0. Previously tracked worst pairs. |
| `do_local` | `int` | If 1, compute per-pair histograms in a 3D array `(nA, nB, hist_len)`. |

#### Returns

A 4-tuple containing:

1. **Global histogram** (`np.ndarray` or `None`): 1D uint64 array where `hist[k]` counts how many (A,B,offset) combinations had exactly `k` matching non-zero positions. Length is `max(H*W)+1` over all arrays in `A_list`. Only returned if `do_hist=1`.

2. **Full match matrices** (`List[List[np.ndarray]]` or `None`): Nested list `[nA][nB]` of int32 arrays. Each array has shape `(Ha+Hb-1, Wa+Wb-1)` containing match counts at each offset. Skipped pairs contain `None`. Only returned if `do_full=1`.

3. **Deprecated** (`None`): Always returns `None`. Previously returned worst pair tracking data.

4. **Local histograms** (`np.ndarray` or `None`): 3D uint32 array of shape `(nA, nB, hist_len)` where `local_hist[i,j,k]` is the count at match level `k` for pair `(A[i], B[j])`. Only returned if `do_local=1`.

#### Algorithm

The C engine performs a "2D equality correlation" - similar to convolution, but instead of multiply+sum, it counts positions where values are exactly equal. Key properties:

- **Zero handling**: Zeros are treated as "don't care" and never contribute to matches. A match only occurs when both `A[y,x] != 0` and `B[y',x'] != 0` and `A[y,x] == B[y',x']`.

- **Offset computation**: For each valid offset `(dy, dx)`, the engine counts matching positions across the overlapping region.

- **Memory layout**: Arrays must be 2D and uint8. The engine handles non-contiguous arrays by copying to contiguous buffers internally.

#### Example

```python
import numpy as np
from eqcorr2d import eqcorr2d_engine

# Create sample handle arrays
A = [np.array([[1, 2, 0], [0, 3, 4]], dtype=np.uint8)]
B = [np.array([[1, 0, 2], [3, 4, 0]], dtype=np.uint8)]

# Compute all pairs, request histogram
mask = np.ones((len(A), len(B)), dtype=np.uint8)
hist, full, _, local = eqcorr2d_engine.compute(
    A, B, mask,
    do_hist=1, do_full=0, do_worst=0, do_local=0
)

print(f"Histogram: {hist}")
# hist[k] = number of offsets with k matching positions
```

## Source Files

The C implementation consists of:

| File | Description |
|------|-------------|
| `c_sources/eqcorr2d_bindings.c` | Python/NumPy bindings, argument parsing, memory management |
| `c_sources/eqcorr2d_core.c` | Core computation kernel (`loop_rot0_mode`) |
| `c_sources/eqcorr2d.h` | Header file with type definitions and function declarations |

## Performance Considerations

- **Memory**: The `do_full=1` option can use significant memory for large arrays. For N arrays of size H×W, full output is N² arrays of size (2H-1)×(2W-1).

- **Rotation handling**: The C engine only computes at 0° orientation. Rotations (90°, 180°, etc.) are handled by the Python wrapper which pre-rotates the B arrays before calling the C engine.

- **Local histograms**: Using `do_local=1` allocates an (nA × nB × hist_len) array. For large handle libraries, this can be substantial.

## Building from Source

The C extension is built automatically during package installation via setuptools. The build requires:

- A C compiler (gcc, clang, or MSVC)
- NumPy development headers
- Python development headers

To rebuild manually:

```bash
cd crisscross_kit
pip install -e .
```

The extension will be compiled to `eqcorr2d/eqcorr2d_engine.cpython-*.so` (or `.pyd` on Windows).
