# Triangular lattice rotation utilities and tests (vectorized, no Python loops)
import numpy as np


def rotate_coords_tri60(i: np.ndarray, j: np.ndarray, k: int = 1):
    """Rotate lattice coordinates by k×60° on a triangular (axial) grid.

    This implements the closed-form rotations for the axial coordinate system
    commonly used with triangular/hexagonal grids. It is fully vectorized and
    supports broadcasting; i and j can be scalars or arrays of the same shape.

    The six distinct rotations (k mod 6) are:
      R:   (i, j) -> (-j,      i + j)
      R^2: (i, j) -> (-(i+j),  i)
      R^3: (i, j) -> (-i,     -j)
      R^4: (i, j) -> (j,      -i - j)
      R^5: (i, j) -> (i + j,  -i)
      R^0: identity (i, j)

    Parameters
    - i, j: np.ndarray or scalars
        Axial indices of equal shape (or broadcastable) representing row/col in
        the triangular lattice embedding used by this project.
    - k: int
        Number of 60° steps (can be any integer; reduced mod 6 internally).

    Returns
    - x, y: rotated coordinates with the same broadcasted shape as inputs.
    """
    k_mod = ((k % 6) + 6) % 6
    if k_mod == 0:
        x, y = i, j
    elif k_mod == 1:
        x, y = -j, i + j
    elif k_mod == 2:
        x, y = -(i + j), i
    elif k_mod == 3:
        x, y = -i, -j
    elif k_mod == 4:
        x, y = j, -i - j
    else:  # k_mod == 5
        x, y = i + j, -i
    return x, y


def rotate_array_tri60(arr: np.ndarray, k: int = 1, map_only_nonzero: bool = False, return_shift: bool = False):
    """Rotate a 2D occupancy array by k×60° on a triangular lattice.

    The array is assumed to live on axial coordinates (i=row, j=col). Rotation
    is implemented by transforming indices, shifting them to be non-negative,
    and scattering values into a tightly sized output array.

    Parameters
    - arr: np.ndarray
        2D input array (e.g., uint8 occupancy). The dtype and sparsity are
        preserved in the output; shape generally changes with rotation.
    - k: int
        Number of 60° steps. Any integer; reduced mod 6 internally.
    - map_only_nonzero: bool
        If True, only the non-zero entries are transformed and written, which is
        typically faster for sparse integer masks.
    - return_shift: bool
        If True, returns a tuple (rotated, shift_x, shift_y) where shift_* are
        the offsets added to make all indices >= 0.

    Returns
    - out: np.ndarray or (np.ndarray, int, int)
        Rotated array; optionally also the integer shifts.

    Notes
    - Because rotation is done in index space, the output shape depends on k and
      the input's footprint on the lattice. Expect different bounding boxes.
    """
    H, W = arr.shape

    if map_only_nonzero:
        # Gather coordinates of the active cells only (sparse-friendly)
        src_i, src_j = np.nonzero(arr)
        src_vals = arr[src_i, src_j]
    else:
        # Dense case: transform the full i,j mesh and scatter values one-to-one
        src_i, src_j = np.meshgrid(np.arange(H), np.arange(W), indexing='ij')
        src_vals = arr

    # Apply the rotation in index space
    x, y = rotate_coords_tri60(src_i, src_j, k=k)

    # Shift to non-negative coordinates for array indexing
    min_x, min_y = int(x.min()), int(y.min())
    shift_x, shift_y = -min_x, -min_y
    xs = x + shift_x
    ys = y + shift_y

    # Allocate tight bounding box and scatter values
    out_H = int(xs.max()) + 1
    out_W = int(ys.max()) + 1
    out = np.zeros((out_H, out_W), dtype=arr.dtype)
    out[xs, ys] = src_vals

    if return_shift:
        return out, shift_x, shift_y
    return out

if __name__ == "__main__":
    # Simple test/demo
    A = np.array([
        [0, 1, 2, 3,4],
        [5, 6, 7, 8, 0]
    ], dtype=np.uint8)

    print("Original array:")
    print(A)

    for k in range(6):
        A_rot = rotate_array_tri60(A, k=k,map_only_nonzero=True)
        print(f"\nRotated by {k*60}°:")
        print(A_rot)