from C_functions.integration_functions import *

# make OpenMP single-threaded (safe with multiprocessing)
os.environ.setdefault("OMP_NUM_THREADS", "1")

def make_random_1xL(n, L, maxval=64):
    return [np.ascontiguousarray(
                np.random.randint(1, maxval + 1, (1, L), dtype=np.uint8))
            for _ in range(n)]




def find_in(max, list_of_list_of_list_of_array):
    report=[]

    for list_of_list_of_array in list_of_list_of_list_of_array:
        for outer, list_of_array in enumerate(list_of_list_of_array):
            for inner, array in enumerate(list_of_array):
                if np.sum(max==array)>0:
                    report.append((outer, inner))

    return list(set(report))

if __name__ == "__main__":


    # Test 1D behavior of python version vs C version, output consistency and speed
    np.random.seed(42)
    noSlats, lenght = 196, 32
    #np.random.seed(42)
    #N, L = 2, 5

    # creat test slat dictionaries with the usual data type
    A_dict = {(1,i): np.random.randint(0, 65, lenght, dtype=np.uint16) for i in range(noSlats)}
    B_dict = {(2,j): np.random.randint(0, 65, lenght, dtype=np.uint16) for j in range(noSlats)}

    # --- C extension (hist only) ---
    runs=3 # increse for better average times
    t0 = time.time()
    for i in range(runs):
        hist_c, r0, r90, r180, r270, worst_pairs = wrap_eqcorr2d(
            A_dict, B_dict,
            rot0=True, rot180=True,rot270=False,rot90=False,
            hist=True, report_full=False, report_worst=True
        )
    print("C time:", round(time.time() - t0, 4), "s")


    # --- C extension (hist with arrays ) ---
    t0 = time.time()
    for i in range(runs):
        hist_c, r0, r90, r180, r270, worst_pairs = wrap_eqcorr2d(
            A_dict, B_dict,
            rot0=True, rot180=True,rot270=False,rot90=False,
            hist=True, report_full=True, report_worst=True
        )
    print("C time with arrays:", round(time.time() - t0, 4), "s")

    # --- C extension (hist and all rotations) ---
    t0 = time.time()
    for i in range(runs):
        hist_c_allrot, r0, r90, r180, r270, worst_pairs = wrap_eqcorr2d(
            A_dict, B_dict,
            rot0=True, rot180=True,rot270=True,rot90=True,
            hist=True, report_full=False, report_worst=True
        )
    print("C time hist and rotations:", round(time.time() - t0, 4), "s")

    # --- C extension (hist and all rotations with smart) ---
    t0 = time.time()
    for i in range(runs):
        hist_c_allrot_smart, r0, r90, r180, r270, worst_pairs = wrap_eqcorr2d(
            A_dict, B_dict,
            rot0=True, rot180=True, rot270=True, rot90=True,
            hist=True, report_full=False, report_worst=True, do_smart=True
        )
    print("C time hist and rotations with dosmart:", round(time.time() - t0, 4), "s")


    # --- C extension (all flags) ---
    t0 = time.time()
    for i in range(runs):
        hist_c_allrot, r0, r90, r180, r270, worst_pairs = wrap_eqcorr2d(
            A_dict, B_dict,
            rot0=True, rot180=True,rot270=True,rot90=True,
            hist=True, report_full=True, report_worst=True
        )
    print("C time all flags no smart:", round(time.time() - t0, 4), "s")

    # Python comparison
    t0 = time.time()
    for i in range(runs):
        matches = lenght - oneshot_hamming_compute(A_dict, B_dict, lenght)
        hist_py = np.bincount(matches.ravel(), minlength=lenght + 1).astype(np.int64)
    print("Python time:", round(time.time() - t0, 4), "s")

    print(" ")
    print("C Histogram 2D:", hist_c_allrot)
    print("C Histogram 1D:", hist_c)
    print("C Histogram 1D all rot smart:", hist_c_allrot_smart)
    print("Python Histogram:", hist_py)


    print(" ")

    # --- Veryfy 2D correctnes ---


 # test arrays , A1 vs B3 hand calculated
    A_2D_dict = {
        "A0": np.array([[0, 0, 2, 2],
                        [3, 2, 1, 3]]),


        "A1": np.array([[1, 2, 1, 3],
                        [3, 0, 0, 0]]),

        "A2": np.array([[1, 2, 2, 2]
                                    ]),

        #"A4": np.array([[0, 0, 0, 0],
        #                [1, 2, 3, 3]]),

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

        #"B4": np.array([[0, 0, 0, 0],
        #                [1, 2, 3, 3]]),
    }

    hist_c_2D, r0_2D, r90_2D, r180_2D, r270_2D, worst_pairs_2D = wrap_eqcorr2d(
        A_2D_dict, B_2D_dict,
        rot0=True,rot90=True, rot180=True,rot270=True,
        hist=True, report_full=True, report_worst=True, do_smart=True
    )

    # compute histogramm by python to cross verify
    pieces = []
    for rot in [r0_2D, r90_2D, r180_2D, r270_2D]:
        if rot is None:  # rotation skipped
            continue
        for row in rot:  # row is always a list
            for a in row:
                if a is not None:  # entry could be None
                    pieces.append(a.ravel())

    flat = np.concatenate(pieces)
    (values, counts) = np.unique(flat, return_counts=True)


    print("2D stuff:")

    print("Histogram 2D from reported Arrays", counts)
    print("Histogram 2D from function  from report", hist_c_2D)


    # find/recompute worst pairs in python to cross verify
    max = max(values)

    worst_paris_2D_recomp = find_in(max, [r0_2D, r90_2D, r180_2D, r270_2D])

    worst_paris_2D_recomp= sorted(worst_paris_2D_recomp)
    worst_paris_2D = sorted(worst_pairs_2D)

    print("C function reported worst:", worst_paris_2D)
    print("Recomputed worst:", worst_paris_2D_recomp)


    # for hand computations pick A1 and B2. rotate clockwise and compare

    print("A1", A_2D_dict["A1"])
    print("B2",B_2D_dict["B2"])

    print("rot 0 deg :")
    print(r0_2D[1][2])
    print("rot 90 deg :")
    print(r90_2D[1][2])
    print("rot 180 deg :")
    print(r180_2D[1][2])
    print("rot 270 deg :")
    print(r270_2D[1][2])