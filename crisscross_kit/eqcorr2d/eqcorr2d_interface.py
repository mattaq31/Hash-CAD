"""
High-level Python interface around the eqcorr2d C engine.

This module provides a thin but well-documented wrapper that:
- Accepts dictionaries of binary handle/antihandle occupancy arrays (1D or 2D)
  keyed by user-facing identifiers.
- Orchestrates optional geometric rotations in Python (0/90/180/270 for square
  lattices; 0/60/120/180/240/300 for triangular lattices) by pre-rotating the
  antihandle arrays before delegating to the C engine. The C core always computes
  for a fixed orientation; we rotate inputs instead of changing the core.
- Aggregates per-rotation outputs into a single, stable result dictionary that is
  easier to consume than the legacy tuple.

Key terms:
- handle_dict: dict[key -> np.ndarray] of uint8 with shape (H, W) or (L,) for 1D
  slats. Non-zero entries indicate occupied positions.
- antihandle_dict: same as handle_dict, but for the opposing set.
- "matchtype": an integer bin used by the C engine to bucket similarity counts.
  Larger values typically represent worse similarity.

Modes:
- classic: only 0° and 180° rotations (historical behavior for 1D slats).
- square_grid: 0°, 90°, 180°, 270°.
- triangle_grid: 0°, 60°, 120°, 180°, 240°, 300° (implemented via rotate_array_tri60).

Smart mode (do_smart):
- If enabled, we still compute 0°/180°.
- For square_grid, 90°/270° are only computed when at least one side of a pair is
  truly 2D (H >= 2 and W >= 2). This keeps compute costs lower for pure 1D data.
- For triangle_grid, the same idea applies to the six-fold rotation set.

Note: This module adds extensive comments and docstrings only. The C code is not
modified by this interface.
"""
import numpy as np
from eqcorr2d import eqcorr2d_engine
from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming, extract_handle_dicts
from crisscross.core_functions.megastructures import Megastructure
from eqcorr2d.rot60 import rotate_array_tri60


def wrap_eqcorr2d(handle_dict, antihandle_dict,
                  mode='classic', hist=True, report_full=False,
                  report_worst=True, do_smart=False):
    """Run eqcorr2d on all handle/antihandle pairs, optionally across rotations.

    This function is the preferred high-level entry point. It accepts two
    dictionaries mapping arbitrary keys (e.g., slat ids) to binary occupancy
    arrays, prepares them for the low-level C engine, optionally pre-rotates the
    antihandles for the requested angle set, and then aggregates all outputs
    into a single, well-structured result dictionary.

    Parameters
    - handle_dict: dict[key -> np.ndarray]
        Binary arrays (uint8), either 1D with shape (L,) or 2D with shape (H, W).
        Non-zeros mark occupied positions. Each array is converted to C-contiguous
        uint8 and reshaped to (1, L) for 1D inputs.
    - antihandle_dict: dict[key -> np.ndarray]
        Same rules as handle_dict.
    - mode: str
        One of 'classic', 'square_grid', or 'triangle_grid'. Determines which
        rotation group is considered:
        • classic: [0, 180]
        • square_grid: [0, 90, 180, 270]
        • triangle_grid: [0, 60, 120, 180, 240, 300]
    - hist: bool
        If True, request histogram accumulation from the C engine. The top-level
        'hist_total' returned here is the sum across all considered rotations.
    - report_full: bool
        If True, per-rotation raw outputs (engine-dependent) are included under
        result['rotations'][angle]['full'].
    - report_worst: bool
        If True, the C engine tracks worst pairs per rotation; this function then
        converts those index pairs into key pairs and, when hist=True, aggregates
        the globally worst key combinations across all rotations.
    - do_smart: bool
        Heuristic compute saver. For square/triangle grids, 90°/270° (and the
        non-axial 60° steps) are only evaluated for pairs where at least one
        operand is truly 2D (H >= 2 and W >= 2). 0°/180° are always evaluated.

    Returns
    dict with the following shape:
    {
      'angles': list[int],                # angles actually computed
      'hist_total': np.ndarray|None,      # summed histogram if hist=True, else None
      'rotations': {
          angle: {
              'hist': np.ndarray|None,        # per-rotation histogram (if hist)
              'full': Any|None,               # per-rotation raw payload (if report_full)
              'worst_pairs_idx': list|None,   # engine index pairs (if report_worst)
              'worst_pairs_keys': list|None,  # same pairs mapped to (handle_key, antihandle_key)
          },
          ...
      },
      'worst_keys_combos': list|None      # all worst key-pairs at the global worst matchtype
    }

    Notes
    - The low-level C engine always computes a single orientation. Rotations are
      handled here by pre-rotating the antihandle arrays B_rot[angle].
    - For triangle_grid, rotations are performed via rotate_array_tri60 which
      maps indices on a triangular lattice. Resultting shapes can change; arrays
      are kept contiguous and in uint8.
    - When hist=False, 'worst_keys_combos' is left as None, because selecting a
      global worst requires the histograms to identify the worst matchtype bin.
    """

    def ensure_2d_uint8(arr):
        arr = np.asarray(arr, dtype=np.uint8)
        if arr.ndim == 1:
            arr = arr[np.newaxis, :]  # (L,) -> (1, L)
        elif arr.ndim != 2:
            raise ValueError(f"Array must be 1D or 2D, got shape {arr.shape}")
        if not arr.flags['C_CONTIGUOUS']:
            arr = np.ascontiguousarray(arr)
        return arr

    def rot90_py(b, k):
        if k == 0:
            out = b

        else:
            out = np.rot90(b, k=k)
        if not out.flags['C_CONTIGUOUS'] or out.dtype != np.uint8:
            out = np.ascontiguousarray(out, dtype=np.uint8)
        return out

    def rot60_py(b, k60):
        """Placeholder for 60-degree rotations used by triangle_grid mode.
        k60 in {0,1,2,3,4,5} corresponds to angles 0,60,120,180,240,300.
        Only 0 (k60=0) and 180 (k60=3) are supported right now; others raise.
        """
        if k60 == 0:
            out = b
        else:
            out = rotate_array_tri60(b, k60, map_only_nonzero=True, return_shift=False)
        if not out.flags['C_CONTIGUOUS'] or out.dtype != np.uint8:
            out = np.ascontiguousarray(out, dtype=np.uint8)
        return out

    # Prepare lists
    handle_keys = list(handle_dict.keys())
    antihandle_keys = list(antihandle_dict.keys())

    A_list = [ensure_2d_uint8(handle_dict[k]) for k in handle_keys]
    B_list = [ensure_2d_uint8(antihandle_dict[k]) for k in antihandle_keys]

    # Decide which rotations to compute respecting do_smart approximation
    anyA2D = any((a.shape[0] >= 2 and a.shape[1] >= 2) for a in A_list)
    anyB2D = any((b.shape[0] >= 2 and b.shape[1] >= 2) for b in B_list)

    # Decide which angles to compute based on mode and do_smart
    mode = (mode or 'square_grid').lower()
    if mode not in ('classic', 'square_grid', 'triangle_grid'):
        raise ValueError("mode must be one of 'classic', 'square_grid', 'triangle_grid'")

    if mode == 'classic':
        angles = [0, 180]
    elif mode == 'square_grid':
        angles = [0, 90, 180, 270]
        if do_smart and not (anyA2D or anyB2D):
            angles = [0, 180]
    else:  # triangle_grid
        # Six rotations: 0,60,120,180,240,300. Only 0 and 180 supported until rot60_py is implemented.
        if do_smart and not (anyA2D or anyB2D):
            angles = [0, 180]
        else:
            angles = [0, 60, 120, 180, 240, 300]

    # Pre-rotate B only for the selected angles
    B_rot = {}
    for angle in angles:
        if mode in ('classic', 'square_grid'):
            k = {0: 0, 90: 1, 180: 2, 270: 3}.get(angle, None)
            if k is None:
                # shouldn't happen in these modes
                raise ValueError(f"Unsupported angle {angle} for mode {mode}")
            B_rot[angle] = [rot90_py(b, k) for b in B_list]
        else:
            # triangle_grid uses 60° steps; currently only 0 and 180 (k60=0 or 3) are implemented
            k60_map = {0: 0, 60: 1, 120: 2, 180: 3, 240: 4, 300: 5}
            k60 = k60_map[angle]
            B_rot[angle] = [rot60_py(b, k60) for b in B_list]

    # Build compute_instructions masks per rotation
    nA, nB = len(A_list), len(B_list)
    ones_mask = np.ones((nA, nB), dtype=np.uint8)
    # Precompute 2D flags per item
    A_is2D = np.array([(a.shape[0] >= 2 and a.shape[1] >= 2) for a in A_list], dtype=bool)
    B_is2D = np.array([(b.shape[0] >= 2 and b.shape[1] >= 2) for b in B_list], dtype=bool)
    pair_need_quarter = np.logical_or(A_is2D[:, None], B_is2D[None, :])
    quarter_mask = pair_need_quarter.astype(np.uint8)

    results_by_rot = {}
    per_rotation = {}
    # Perform calls per selected rotation
    for angle in angles:
        if angle in (0, 180):
            mask = ones_mask
        else:
            # 90/270: if do_smart enabled, use selective mask; else full ones
            mask = quarter_mask if do_smart else ones_mask
        res = eqcorr2d_engine.compute(A_list, B_rot[angle], mask, int(hist), int(report_full), int(report_worst))
        results_by_rot[angle] = res
        # Prepare per-rotation entry with both index and key-wise worst pairs
        hist_a = res[0] if hist else None
        full_a = res[1] if report_full else None
        worst_idx = res[2] if report_worst else None
        worst_keys = None
        if report_worst and worst_idx is not None:
            worst_keys = []
            for tubel in worst_idx:
                iA, iB = tubel[0], tubel[1]
                worst_keys.append((handle_keys[iA], antihandle_keys[iB]))
        per_rotation[angle] = {
            'hist': hist_a,
            'full': full_a,
            'worst_pairs_idx': worst_idx,
            'worst_pairs_keys': worst_keys,
        }

    # Aggregate histogram across angles (if requested)
    agg_hist = None
    if hist:
        for angle in angles:
            res = results_by_rot.get(angle)
            if not res:
                continue
            h = res[0]
            if h is None:
                continue
            if agg_hist is None:
                agg_hist = np.array(h, dtype=np.int64, copy=True)
            else:
                L = max(len(agg_hist), len(h))
                if len(agg_hist) < L:
                    tmp = np.zeros(L, dtype=np.int64)
                    tmp[:len(agg_hist)] = agg_hist
                    agg_hist = tmp
                if len(h) < L:
                    hh = np.zeros(L, dtype=np.int64)
                    hh[:len(h)] = h
                else:
                    hh = h
                agg_hist[:L] += hh[:L]

    # Determine the true global worst across all rotations and collect all worst pairs
    worst_keys_combos = None
    if report_worst:
        # We require hist=True to reliably identify the worst match value across rotations
        # (the C worst tracker does not expose the max value). If hist is False, leave None.
        if hist:
            worst_per_rot = {}
            for angle in angles:
                res = results_by_rot.get(angle)
                if not res:
                    continue
                h = res[0]
                if h is None:
                    continue
                # worst index = highest bin with nonzero count
                worst = None
                for matchtype, count in enumerate(h):
                    if count != 0:
                        worst = matchtype
                if worst is not None:
                    worst_per_rot[angle] = worst

            if worst_per_rot:
                global_worst = max(worst_per_rot.values())
                # Collect all worst pairs from every rotation that achieves the global worst
                combo_set = set()
                for angle, widx in worst_per_rot.items():
                    if widx != global_worst:
                        continue
                    wpairs = results_by_rot.get(angle, (None, None, None))[2]
                    if wpairs is None:
                        continue
                    for tubel in wpairs:
                        iA, iB = tubel[0], tubel[1]
                        combo_set.add((handle_keys[iA], antihandle_keys[iB]))
                worst_keys_combos = sorted(combo_set)  # stable order for tests
            else:
                worst_keys_combos = []
        else:
            worst_keys_combos = None

    return {
        'angles': angles,
        'hist_total': agg_hist,
        'rotations': per_rotation,
        'worst_keys_combos': worst_keys_combos,
    }


def get_worst_match(c_results):
    """Return the worst (highest non-zero) matchtype from a result.
    Supports both the new dict return from wrap_eqcorr2d and the legacy tuple.
    """
    if isinstance(c_results, dict):
        hist = c_results.get('hist_total')
    else:
        hist = c_results[0]
    if hist is None:
        return None
    worst = None
    for matchtype, count in enumerate(hist):
        if count != 0:
            worst = matchtype
    return worst


def get_sum_score(c_results, fudge_dg=-10):
    """Compute a weighted sum score from histogram.
    Accepts both the new dict return and the legacy tuple.
    """
    if isinstance(c_results, dict):
        hist = c_results.get('hist_total')
    else:
        hist = c_results[0]
    if hist is None:
        return 0.0
    summe = 0.0
    for matchtype, count in enumerate(hist):
        summe = summe + count * np.exp(-fudge_dg * matchtype)
    return summe


def get_seperate_worst_lists(c_results):
    """Return separate lists of worst handle and antihandle identifiers.
    Accepts both new dict and legacy tuple results.
    For the new dict, worst_keys_combos are already keys, not indices.
    """
    if isinstance(c_results, dict):
        worst = c_results.get('worst_keys_combos') or []
        handle_list = [h for (h, _a) in worst]
        antihandle_list = [a for (_h, a) in worst]
        return (handle_list, antihandle_list)
    else:
        worst = c_results[5]
        handle_list = []
        antihandle_list = []
        for tuble in worst:
            handle_list.append(tuble[0])
            antihandle_list.append(tuble[1])
        return (handle_list, antihandle_list)


# Do not use this. It would only work if all 1D slats are fully occupied with handles and antihandles

def compensate_do_smart(hist, handle_dict, antihandle_dict, standart_slat_lenght=32, libraray_length=64):
    """Attempt to post-correct histograms when do_smart skipped 90°/270° cases.

    WARNING: This correction only makes sense under very restrictive assumptions
    and is disabled in normal workflows. It assumes all involved 1D slats are
    fully occupied across a fixed standard length and then injects an expected
    distribution for the left-out orientations based on a simple library-size
    probability model. If your slats are sparse or lengths vary, this will be
    inaccurate. Prefer computing the full rotation set if you need exact stats.

    Parameters
    - hist: np.ndarray
        Aggregated histogram to be adjusted.
    - handle_dict / antihandle_dict: dict
        Used only to estimate how many 1D×1D pairs were skipped.
    - standart_slat_lenght: int
        Assumed length for 1D slats when estimating left-out entries.
    - libraray_length: int
        Size of the handle library used to estimate p0 = 1/library_length.

    Returns
    - corrected_hist: np.ndarray with the estimated counts added to bins 0 and 1.
    """
    # extract values from dicts
    handles = list(handle_dict.values())
    antihandles = list(antihandle_dict.values())
    # count 1D and 2D handles in a loop
    count_1D_handles = 0
    count_2D_handles = 0
    for handle in handles:
        if handle.shape[0] == 1:
            count_1D_handles = count_1D_handles + 1
        else:
            count_2D_handles = count_2D_handles + 1
    # count 1D and 2D antihandles in a loop
    count_1D_antihandles = 0
    count_2D_antihandles = 0
    for antihandle in antihandles:
        if antihandle.shape[0] == 1:
            count_1D_antihandles = count_1D_antihandles + 1
        else:
            count_2D_antihandles = count_2D_antihandles + 1
    # calculate number of combinations not tested by do_smart
    not_tested_combinations = count_1D_handles * count_1D_antihandles * 2  # times 2 for 90 and 270
    left_out_array_lenght = (standart_slat_lenght + 1 - 1) * (
                standart_slat_lenght + 1 - 1)  # this is number of entries of the result arrays not computed
    all_left_out_entries = not_tested_combinations * left_out_array_lenght
    # now calculate expected distribution of these combinations. since the dimension is only 1D of each we can eighter have a matchtype 1 ore 0.
    # the probability for a matchtype 0 is 1/libraray_length
    p0 = 1 / libraray_length
    hit1 = all_left_out_entries * p0
    hit0 = all_left_out_entries * (1 - p0)
    # now add these to the histogram
    corrected_hist = hist.copy()
    corrected_hist[0] = corrected_hist[0] + int(hit0)
    corrected_hist[1] = corrected_hist[1] + int(hit1)

    return corrected_hist


def get_similarity_hist(handle_dict, antihandle_dict, mode='square_grid'):
    """Build a library-level similarity histogram (handles+antihandles).

    This helper runs wrap_eqcorr2d twice, once within the handle set and once
    within the antihandle set, then sums the resulting histograms. Finally it
    subtracts a simple self-match correction so that exact self-pairs do not
    inflate the counts.

    Notes
    - Only the aggregated histogram is returned in the output dict (under
      'hist_total'). Per-rotation details are not computed here.
    - The self-match correction subtracts one count at matchtype = number of
      nonzeros for each individual array. This assumes the engine would count a
      self-pair as a perfect overlap at that bin.
    """
    # Compute pairwise stats within the handle set
    res_hh = wrap_eqcorr2d(handle_dict, handle_dict,
                           mode=mode,
                           hist=True, report_full=False, report_worst=False)
    hist_hh = res_hh['hist_total']

    # Compute pairwise stats within the antihandle set
    res_ahah = wrap_eqcorr2d(antihandle_dict, antihandle_dict,
                             mode=mode,
                             hist=True, report_full=False, report_worst=True)
    hist_ahah = res_ahah['hist_total']

    # Sum with safe length alignment
    length = max(len(hist_hh), len(hist_ahah))
    hist_combined = np.zeros(length)
    hist_combined[:len(hist_hh)] += hist_hh
    hist_combined[:len(hist_ahah)] += hist_ahah

    # Build self-match correction vector and subtract
    correction = np.zeros(length)
    for handle in list(handle_dict.values()):
        # A self pair contributes to the bin equal to its number of non-zeros
        self_match = np.count_nonzero(handle)
        correction[self_match] = correction[self_match] + 1

    for antihandle in list(antihandle_dict.values()):
        self_match = np.count_nonzero(antihandle)
        correction[self_match] = correction[self_match] + 1

    corrected_result = hist_combined - correction

    return {
        'angles': [],                # no per-rotation info for this helper
        'hist_total': corrected_result,
        'rotations': {},
        'worst_keys_combos': None,
    }


if __name__ == "__main__":
    # example integration

    megastructure = Megastructure(
        import_design_file="C:/Users\Flori\Dropbox\CrissCross\Papers\hash_cad\design_library\hexagon\hexagon_design_hashcad_seed.xlsx")
    slat_array = megastructure.generate_slat_occupancy_grid()
    handle_array = megastructure.generate_assembly_handle_grid()

    old_dict_results = multirule_oneshot_hamming(slat_array, handle_array,
                                                 report_worst_slat_combinations=True,
                                                 per_layer_check=False,
                                                 specific_slat_groups=None,
                                                 request_substitute_risk_score=True,
                                                 slat_length=32,
                                                 partial_area_score=False,
                                                 return_match_histogram=True)

    handle_slats, antihandle_slats = extract_handle_dicts(handle_array, slat_array)
    print("hallo")

    r_c = wrap_eqcorr2d(handle_slats, antihandle_slats)

    worst_match_type = get_worst_match(r_c)

    sum_score = get_sum_score(r_c)

    worst_handles, worst_antihandles = get_seperate_worst_lists(r_c)

    mean_score = sum_score / (len(handle_slats) * len(antihandle_slats))  # this one seems to be the smarter choice
    mean_score_old = mean_score / 126

    sim_hist = get_similarity_hist(handle_slats, antihandle_slats)

    worst_sim_match = get_worst_match(sim_hist)
