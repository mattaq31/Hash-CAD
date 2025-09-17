# crisscross_kit/crisscross/C_functions/debug_driver.py
# Small Python entry for C-side debugger. Keeps test logic in Python so C stays minimal.

import numpy as np
from crisscross.C_functions.integration_functions import wrap_eqcorr2d


def debug_entry():
    """Build tiny 2D test dicts and call wrap_eqcorr2d to drive the C extension.
    Prints a couple of summaries so you see progress in the console.
    """
    A_2D_dict = {
        'A0': np.array([[0, 0, 2, 2], [3, 2, 1, 3]], dtype=np.uint8),
        'A1': np.array([[1, 2, 1, 3], [3, 0, 0, 0]], dtype=np.uint8),
        'A2': np.array([[1, 2, 2, 2]], dtype=np.uint8),
    }
    B_2D_dict = {
        'B0': np.array([[0, 0, 3, 1, 1, 2]], dtype=np.uint8),
        'B1': np.array([[0, 0, 3, 0, 0, 0]], dtype=np.uint8),
        'B2': np.array([[0, 0, 3], [1, 1, 2]], dtype=np.uint8),
        'B3': np.array([[1, 2, 0, 0, 3], [1, 1, 2, 1, 2]], dtype=np.uint8),
    }
    print('[debug_driver] Calling wrap_eqcorr2d ...')
    hist_c_2D, r0_2D, r90_2D, r180_2D, r270_2D, worst_pairs_2D = wrap_eqcorr2d(
        A_2D_dict, B_2D_dict,
        rot0=True, rot90=True, rot180=True, rot270=True,
        hist=True, report_full=True, report_worst=True
    )
    print('[debug_driver] hist length:', len(hist_c_2D) if hist_c_2D is not None else None)
    print('[debug_driver] worst pairs sample:', (worst_pairs_2D[:3] if worst_pairs_2D else None))
