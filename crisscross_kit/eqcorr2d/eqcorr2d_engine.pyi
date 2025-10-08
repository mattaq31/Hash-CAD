from typing import List, Optional, Sequence, Tuple
import numpy as np

# A_list and B_list: sequences of 2D uint8 arrays

def compute(
    A_list: Sequence[np.ndarray],
    B_list: Sequence[np.ndarray],
    compute_instructions: Sequence[np.ndarray],
    do_hist: int,
    do_full: int,
    report_worst: int,
    local_histogram: int = 0,
) -> Tuple[
    Optional[np.ndarray],
    Optional[List[List[np.ndarray]]],
    Optional[np.ndarray],  # worst-count matrix (deprecated, always None)
    Optional[np.ndarray],  # local hist per pair as 3D ndarray (nA,nB,hdim), uint32
]: ...
