from typing import List, Optional, Sequence, Tuple
import numpy as np

# A_list and B_list: sequences of 2D uint8 arrays
Array2DU8 = np.ndarray

def compute(
    A_list: Sequence[Array2DU8],
    B_list: Sequence[Array2DU8],
    rot0: int,
    rot90: int,
    rot180: int,
    rot270: int,
    do_hist: int,
    do_full: int,
    report_worst: int,
) -> Tuple[
    Optional[np.ndarray],
    Optional[List[List[np.ndarray]]],
    Optional[List[List[np.ndarray]]],
    Optional[List[List[np.ndarray]]],
    Optional[List[List[np.ndarray]]],
    Optional[List[Tuple[int, int]]],
]: ...
