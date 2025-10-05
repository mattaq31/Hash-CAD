import time
from eqcorr2d.eqcorr2d_interface import *
from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import oneshot_hamming_compute


def make_random_1xL(n, L, maxval=64):
    return [np.ascontiguousarray(
        np.random.randint(1, maxval + 1, (1, L), dtype=np.uint8))
        for _ in range(n)]


def find_in(max, list_of_list_of_list_of_array):
    report = []

    for list_of_list_of_array in list_of_list_of_list_of_array:
        for outer, list_of_array in enumerate(list_of_list_of_array):
            for inner, array in enumerate(list_of_array):
                if np.sum(max == array) > 0:
                    report.append((outer, inner))

    return list(set(report))


if __name__ == "__main__":

    # Test 1D behavior of python version vs C version, output consistency and speed
    np.random.seed(42)
    noSlats, length = 196, 32
    # np.random.seed(42)
    # N, L = 2, 5

    # creat test slat dictionaries with the usual data type
    A_dict = {(1,i): np.random.randint(0, 65, length, dtype=np.uint8) for i in range(noSlats)}
    B_dict = {(2,j): np.random.randint(0, 65, length, dtype=np.uint8) for j in range(noSlats)}

    # --- C extension (hist only) ---
    runs = 3  # increse for better average times
    t0 = time.time()
    for i in range(runs):
        res_c = wrap_eqcorr2d(
            A_dict, B_dict,
            mode='classic',
            hist=True, report_full=False, report_worst=True,do_smart=False
        )
    print("C time:", round(time.time() - t0, 4), "s")
    hist_c = res_c['hist_total']

    # --- C extension (hist with arrays ) ---
    t0 = time.time()
    for i in range(runs):
        res_c_arrays = wrap_eqcorr2d(
            A_dict, B_dict,
            mode='classic',
            hist=True, report_full=True, report_worst=True
        )
    print("C time with arrays:", round(time.time() - t0, 4), "s")
    r0 = res_c_arrays['rotations'].get(0, {}).get('full')
    r90 = res_c_arrays['rotations'].get(90, {}).get('full')
    r180 = res_c_arrays['rotations'].get(180, {}).get('full')
    r270 = res_c_arrays['rotations'].get(270, {}).get('full')

    # --- C extension (hist and all rotations) ---
    t0 = time.time()
    for i in range(runs):
        res_allrot = wrap_eqcorr2d(
            A_dict, B_dict,
            mode='square_grid',
            hist=True, report_full=False, report_worst=True
        )
    print("C time hist and rotations:", round(time.time() - t0, 4), "s")
    hist_c_allrot = res_allrot['hist_total']

    # --- C extension (hist and all rotations with smart) ---
    t0 = time.time()
    for i in range(runs):
        res_allrot_smart = wrap_eqcorr2d(
            A_dict, B_dict,
            mode='square_grid',
            hist=True, report_full=False, report_worst=True, do_smart=True
        )
    print("C time hist and rotations with dosmart:", round(time.time() - t0, 4), "s")
    hist_c_allrot_smart = res_allrot_smart['hist_total']


    # --- C extension (all flags) ---

    t0 = time.time()
    for i in range(runs):
        res_allflags = wrap_eqcorr2d(
            A_dict, B_dict,
            hist=True,mode="square_grid", report_full=True, report_worst=True, do_smart=False
        )
    print("C time all flags no smart:", round(time.time() - t0, 4), "s")
    hist_c_allrot = res_allflags['hist_total']

    # Python comparison
    t0 = time.time()
    for i in range(runs):
        matches = length - oneshot_hamming_compute(A_dict, B_dict, length)
        hist_py = np.bincount(matches.ravel(), minlength=length + 1).astype(np.int64)
    print("Python time:", round(time.time() - t0, 4), "s")

    print(" ")
    print("C Histogram 2D:", hist_c_allrot)
    print("C Histogram 1D:", hist_c)
    print("C Histogram 1D all rot smart:", hist_c_allrot_smart)
    print("Python Histogram:", hist_py)

    print(" ")

    # --- Verify 2D correctness ---

    # test arrays , A1 vs B3 hand calculated
    A_2D_dict = {
        "A0": np.array([[0, 0, 2, 2],
                        [3, 2, 1, 3]]),

        "A1": np.array([[1, 2, 1, 3],
                        [0, 3, 1, 1]]),

        "A2": np.array([[1, 2, 2, 2]
                        ]),

        # "A4": np.array([[0, 0, 0, 0],
        #                [1, 2, 3, 3]]),

    }

    B_2D_dict = {

        "B0": np.array([[0, 0, 3, 1, 1, 2]
                        ]),
        "B1": np.array([[0, 0, 3, 0, 0, 0]
                        ]),

        "B2": np.array([[0, 2, 3],
                        [1, 1, 2]]),
        "B3": np.array([[1, 2, 0, 0, 3],
                        [1, 1, 2, 1, 2]]),

        # "B4": np.array([[0, 0, 0, 0],
        #                [1, 2, 3, 3]]),
    }

    res_2D = wrap_eqcorr2d(
        A_2D_dict, B_2D_dict,
        mode='square_grid',
        hist=True, report_full=True, report_worst=True, do_smart=True
    )

    r0_2D   = res_2D['rotations'].get(0, {}).get('full')
    r90_2D  = res_2D['rotations'].get(90, {}).get('full')
    r180_2D = res_2D['rotations'].get(180, {}).get('full')
    r270_2D = res_2D['rotations'].get(270, {}).get('full')

    # compute histogramm by python to cross verify
    pieces = []
    for rot in [r0_2D, r90_2D, r180_2D, r270_2D]:
        if rot is None:  # rotation skipped
            continue
        for row in rot:  # row is always a list
            for a in row:
                if a is not None:  # entry could be None
                    pieces.append(a.ravel())

    flat = np.concatenate(pieces) if pieces else np.array([], dtype=np.int32)
    (values, counts) = (None, None)
    if flat.size > 0:
        (values, counts) = np.unique(flat, return_counts=True)

    print("2D stuff 90 deg:")

    print("Histogram 2D from reported Arrays", counts)
    print("Histogram 2D from function  from report", res_2D['hist_total'])

    # find/recompute worst pairs in python to cross verify
    if values is not None and len(values) > 0:
        maxv = max(values)
        worst_paris_2D_recomp = find_in(maxv, [r0_2D, r90_2D, r180_2D, r270_2D])
        worst_paris_2D_recomp = sorted(worst_paris_2D_recomp)
    else:
        worst_paris_2D_recomp = []
    worst_paris_2D = sorted(res_2D['worst_keys_combos'] or [])

    print("C function reported worst:", worst_paris_2D)
    print("Recomputed worst:", worst_paris_2D_recomp)

    # for hand computations pick A1 and B2. rotate clockwise and compare

    print("A1", A_2D_dict["A1"])
    print("B2", B_2D_dict["B2"])

    print("rot 0 deg :")
    print(r0_2D[1][2])
    print("rot 90 deg :")
    print(r90_2D[1][2])
    print("rot 180 deg :")
    print(r180_2D[1][2])
    print("rot 270 deg :")
    print(r270_2D[1][2])


# --- 60° triangular grid tests mirroring the 90° square tests ---
    res_2D_tri = wrap_eqcorr2d(
        A_2D_dict, B_2D_dict,
        mode='triangle_grid',
        hist=True, report_full=True, report_worst=True, do_smart=True
    )

    rt0    = res_2D_tri['rotations'].get(0,   {}).get('full')
    rt60   = res_2D_tri['rotations'].get(60,  {}).get('full')
    rt120  = res_2D_tri['rotations'].get(120, {}).get('full')
    rt180  = res_2D_tri['rotations'].get(180, {}).get('full')
    rt240  = res_2D_tri['rotations'].get(240, {}).get('full')
    rt300  = res_2D_tri['rotations'].get(300, {}).get('full')

    pieces_tri = []
    for rot in [rt0, rt60, rt120, rt180, rt240, rt300]:
        if rot is None:
            continue
        for row in rot:
            for a in row:
                if a is not None:
                    pieces_tri.append(a.ravel())

    flat_tri = np.concatenate(pieces_tri) if pieces_tri else np.array([], dtype=np.int32)
    (values_tri, counts_tri) = (None, None)
    if flat_tri.size > 0:
        (values_tri, counts_tri) = np.unique(flat_tri, return_counts=True)

    print("2D stuff 60 deg (triangle grid):")
    print("Histogram 2D (triangle) from reported Arrays", counts_tri)
    print("Histogram 2D (triangle) from function from report", res_2D_tri['hist_total'])

    if values_tri is not None and len(values_tri) > 0:
        maxv_tri = max(values_tri)
        worst_pairs_2D_tri_recomp = find_in(maxv_tri, [rt0, rt60, rt120, rt180, rt240, rt300])
        worst_pairs_2D_tri_recomp = sorted(worst_pairs_2D_tri_recomp)
    else:
        worst_pairs_2D_tri_recomp = []
    worst_pairs_2D_tri = sorted(res_2D_tri['worst_keys_combos'] or [])

    print("C function reported worst (triangle):", worst_pairs_2D_tri)
    print("Recomputed worst (triangle):", worst_pairs_2D_tri_recomp)

    # For hand computations pick A1 and B2 again; show all six rotations
    print("A1", A_2D_dict["A1"]) 
    print("B2", B_2D_dict["B2"]) 

    print("rot 0 deg (tri):")
    print(rt0[1][2])
    print("rot 60 deg:")
    print(rt60[1][2])
    print("rot 120 deg:")
    print(rt120[1][2])
    print("rot 180 deg:")
    print(rt180[1][2])
    print("rot 240 deg:")
    print(rt240[1][2])
    print("rot 300 deg:")
    print(rt300[1][2])
