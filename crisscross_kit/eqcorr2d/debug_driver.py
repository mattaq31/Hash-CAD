# crisscross_kit/crisscross/C_functions/debug_driver.py
# Small Python entry for C-side debugger. Keeps test logic in Python so C stays minimal.

import os
import time
import numpy as np
from crisscross.C_functions.integration_functions import wrap_eqcorr2d, oneshot_hamming_compute


def make_random_1d(n, L, maxval=64):
    return [np.random.randint(0, maxval, L, dtype=np.uint8) for _ in range(n)]


def make_spiced_2d(arr_1d):
    L = arr_1d.size
    assert L % 2 == 0, "length must be even to split into two rows"
    return arr_1d.reshape((2, L // 2))


def debug_entry():
    # make OpenMP single-threaded (safe with multiprocessing)
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    print("[debug_driver] debug_entry entered")
    np.random.seed(42)
    no_slats = 196
    length = 32

    # Build base 1D dictionaries
    A_dict = {(1, i): np.random.randint(0, 65, length, dtype=np.uint8) for i in range(no_slats)}
    B_dict = {(2, j): np.random.randint(0, 65, length, dtype=np.uint8) for j in range(no_slats)}

    # Spice in some true 2D arrays (half length, two rows)
    n_spice = 8
    spiced_indices_A = list(np.random.choice(no_slats, size=n_spice, replace=False))
    spiced_indices_B = list(np.random.choice(no_slats, size=n_spice, replace=False))

    for idx in spiced_indices_A:
        key = (1, idx)
        arr1d = A_dict[key]
        A_dict[key] = make_spiced_2d(arr1d)
    for idx in spiced_indices_B:
        key = (2, idx)
        arr1d = B_dict[key]
        B_dict[key] = make_spiced_2d(arr1d)

    # Collect results in a dict keyed by compact flag-summary strings
    results = {}

    runs = 3

    # 1) hist + rot0 + rot180 + report_worst
    key = "hist,rot0,rot180,report_worst"
    t0 = time.time()
    res = None
    for i in range(runs):
        res = wrap_eqcorr2d(
            A_dict, B_dict,
            mode='classic',
            hist=True, report_full=False, report_worst=True
        )
    elapsed = round(time.time() - t0, 4)
    results[key] = (res, elapsed)
    print(f"[debug_driver] {key} time: {elapsed} s")

    # 2) hist + rot0 + rot180 + report_full + report_worst
    key = "hist,rot0,rot180,report_full,report_worst"
    t0 = time.time()
    res = None
    for i in range(runs):
        res = wrap_eqcorr2d(
            A_dict, B_dict,
            mode='classic',
            hist=True, report_full=True, report_worst=True
        )
    elapsed = round(time.time() - t0, 4)
    results[key] = (res, elapsed)
    print(f"[debug_driver] {key} time: {elapsed} s")

    # 3) hist + all rotations + report_worst
    key = "hist,rot0,rot90,rot180,rot270,report_worst"
    t0 = time.time()
    res = None
    for i in range(runs):
        res = wrap_eqcorr2d(
            A_dict, B_dict,
            mode='square_grid',
            hist=True, report_full=False, report_worst=True
        )
    elapsed = round(time.time() - t0, 4)
    results[key] = (res, elapsed)
    print(f"[debug_driver] {key} time: {elapsed} s")

    # 4) hist + all rotations + report_worst + do_smart
    key = "hist,rot0,rot90,rot180,rot270,report_worst,do_smart"
    t0 = time.time()
    res = None
    for i in range(runs):
        res = wrap_eqcorr2d(
            A_dict, B_dict,
            rot0=True, rot180=True, rot270=True, rot90=True,
            hist=True, report_full=False, report_worst=True, do_smart=True
        )
    elapsed = round(time.time() - t0, 4)
    results[key] = (res, elapsed)
    print(f"[debug_driver] {key} time: {elapsed} s")

    # 5) hist + all rotations + report_full + report_worst
    key = "hist,rot0,rot90,rot180,rot270,report_full,report_worst"
    t0 = time.time()
    res = None
    for i in range(runs):
        res = wrap_eqcorr2d(
            A_dict, B_dict,
            rot0=True, rot180=True, rot270=True, rot90=True,
            hist=True, report_full=True, report_worst=True
        )
    elapsed = round(time.time() - t0, 4)
    results[key] = (res, elapsed)
    print(f"[debug_driver] {key} time: {elapsed} s")

    # 6) hist + all rotations + report_full + report_worst + do_smart
    key = "hist,rot0,rot90,rot180,rot270,report_full,report_worst,do_smart"
    t0 = time.time()
    res = None
    for i in range(runs):
        res = wrap_eqcorr2d(
            A_dict, B_dict,
            rot0=True, rot180=True, rot270=True, rot90=True,
            hist=True, report_full=True, report_worst=True, do_smart=True
        )
    elapsed = round(time.time() - t0, 4)
    results[key] = (res, elapsed)
    print(f"[debug_driver] {key} time: {elapsed} s")

    # Store the spiced indices for later verification
    results["spiced_indices"] = (spiced_indices_A, spiced_indices_B)

    # Python comparison: run the original (unconditional) python compare only when
    # no spiced 2D arrays were injected (n_spice == 0). Otherwise skip it.
    key = "python_hist_compare"
    hist_py = None
    elapsed = 0.0
    if n_spice == 0:
        t0 = time.time()
        for i in range(runs):
            matches = length - oneshot_hamming_compute(A_dict, B_dict, length)
            hist_py = np.bincount(matches.ravel(), minlength=length + 1).astype(np.int64)
        elapsed = round(time.time() - t0, 4)
        print(f"[debug_driver] {key} time: {elapsed} s")
    else:
        # skip expensive Python recompute when we injected true 2D arrays
        hist_py = None
        elapsed = 0.0
        print(f"[debug_driver] {key} skipped (spiced 2D arrays present)")
    results[key] = (hist_py, elapsed)

    # 2D verification block — keep as a stored result
    A_2D_dict = {
        "A0": np.array([[0, 0, 2, 2],
                        [3, 2, 1, 3]]),

        "A1": np.array([[1, 2, 1, 3],
                        [3, 0, 0, 0]]),

        "A2": np.array([[1, 2, 2, 2]
                                    ]),
    }

    B_2D_dict = {
        "B0": np.array([[0, 0, 3,1,1,2]
                                ]),
        "B1": np.array([[0, 0, 3, 0, 0, 0]
                        ]),

        "B2": np.array([[0, 0, 3],
                        [1, 1, 2]]),
        "B3": np.array([[1, 2, 0,0,3],
                        [1, 1, 2,1,2]]),
    }

    key = "2D_test_full_reports"
    t0 = time.time()
    res_2d = wrap_eqcorr2d(
        A_2D_dict, B_2D_dict,
        mode='square_grid',
        hist=True, report_full=True, report_worst=True, do_smart=True
    )
    elapsed = round(time.time() - t0, 4)
    # also compute flattened histogram from returned full maps for cross-check
    # Build histogram pieces from per-rotation full arrays
    r0_2D   = res_2d['rotations'].get(0, {}).get('full')
    r90_2D  = res_2d['rotations'].get(90, {}).get('full')
    r180_2D = res_2d['rotations'].get(180, {}).get('full')
    r270_2D = res_2d['rotations'].get(270, {}).get('full')
    pieces = []
    for rot in [r0_2D, r90_2D, r180_2D, r270_2D]:
        if rot is None:
            continue
        for row in rot:
            for a in row:
                if a is not None:
                    pieces.append(a.ravel())
    flat = np.concatenate(pieces) if pieces else np.array([], dtype=np.int32)
    values, counts = (None, None)
    if flat.size > 0:
        values, counts = np.unique(flat, return_counts=True)
    results[key] = (res_2d, (values, counts, elapsed))
    print(f"[debug_driver] {key} time: {elapsed} s")

    # Return the aggregated results dictionary for inspection from C debugger
    print("DEBUG_DRIVER: DONE")
    return results, spiced_indices_A, spiced_indices_B


if __name__ == "__main__":
   res_dict, spiceA, spiceB = debug_entry()
