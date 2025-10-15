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
from eqcorr2d.rot60 import rotate_array_tri60
from collections import Counter


def comprehensive_score_analysis(handle_dict, antihandle_dict, match_counts, connection_graph, connection_angle,
                                 do_worst=False, fudge_dg=10, request_similarity_score=True):
    """
    When provided with a megastructure's slat handles/antihandles and connection graphs, this function computes
    all relevant match count metrics including worst match, mean log score, similarity score, and a compensated match histogram.
    :param handle_dict: Dictionary of slat handle arrays (can be 1D or 2D).
    :param antihandle_dict: Dictionary of slat antihandle arrays (can be 1D or 2D).
    :param match_counts: Dictionary with counts of expected matches due to connections between slats.
    :param connection_graph: Dictionary mapping match types to lists of (handle_key, antihandle_key) pairs that are expected to match due to connections.
    :param connection_angle: Either '60' or '90' indicating the connection geometry.
    :param do_worst: Set to true to return which slat pairs contributed to the worst match score.
    :param fudge_dg: Fudge factor for mean log score computation.
    :param request_similarity_score: If True, computes a similarity score to check for slat duplication risk.
    :return: Dictionary with all data.
    """
    # runs the match comparison computation using our eqcorr2D C function
    if do_worst:
        local_histogram = True
    else:
        local_histogram = False

    full_results = wrap_eqcorr2d(handle_dict, antihandle_dict, do_smart=True, hist=True, local_histogram=local_histogram,
                                 mode='triangle_grid' if connection_angle == '60' else 'square_grid')

    # compensates for matches in the design that are expected based on slat connections
    hist = full_results['hist_total']
    match_counts_histogram = np.zeros_like(hist)
    for match, count in match_counts.items():
        if match > 1:
            match_counts_histogram[match] += count

    comp_hist = compensate_histogram(hist, match_counts_histogram)
    full_results['hist_total'] = comp_hist

    # extracts the worst match score, already compensated for connections. so from here on only true worsts can be computed
    worst_match = get_worst_match(full_results)

    # truncates the histogram to prevent numerical instability in sum score analysis. should no longer be necessary
    full_results['hist_total'] = full_results['hist_total'][:worst_match + 1]
    mean_log_score = np.log(get_sum_score(full_results, fudge_dg=fudge_dg) / (len(handle_dict) * len(antihandle_dict)))/fudge_dg

    data_dict = {'worst_match_score': worst_match, 'mean_log_score': mean_log_score,
                 'match_histogram': full_results['hist_total'],
                 'uncompensated_match_histogram': hist}

    if request_similarity_score:
        # runs a separate similarity analysis to check for slats that are too similar to each other.
        similarity_results = get_similarity_hist(handle_dict, antihandle_dict, mode='triangle_grid' if connection_angle == '60' else 'square_grid')
        similarity_score = get_worst_match(similarity_results)
        data_dict['similarity_score'] = similarity_score

    if do_worst:
        data_dict['worst_slat_combos'] = get_compensated_worst_keys_combos(full_results, connection_graph)

    return data_dict

def compensate_histogram(hist, connection_hist):
    """Subtract the connection occupancy from the total histogram safely.
    Handles unequal lengths by padding the shorter array with zeros.
    """
    hist = np.asarray(hist, dtype=int)
    connection_hist = np.asarray(connection_hist, dtype=int)

    # zero out the entry for key=1 (ignored in smart mode)
    if connection_hist.size > 1:
        connection_hist[1] = 0

    # pad shorter array so shapes match
    max_len = max(len(hist), len(connection_hist))
    hist_padded = np.zeros(max_len, dtype=int)
    conn_padded = np.zeros(max_len, dtype=int)

    hist_padded[:len(hist)] = hist
    conn_padded[:len(connection_hist)] = connection_hist

    # compute compensated histogram
    comphist = hist_padded - conn_padded
    if np.any(comphist < 0):
        raise ValueError("Negative values detected in comphist — possible over-subtraction.")

    return comphist

def make_connection_histogram(connection_graph):
    """Return a histogram where each index corresponds to a key in connection_graph,
    and the value is the number of connections (list length) for that key."""

    max_key = max(connection_graph.keys())
    con_hist = np.zeros(max_key + 1, dtype=int)

    for key, connections in connection_graph.items():
        con_hist[key] = len(connections)

    return con_hist

def wrap_eqcorr2d(handle_dict, antihandle_dict,
                  mode='classic', hist=True, local_histogram=False, report_full=False,
                   do_smart=False):
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
        """60° rotations for triangle_grid.
        For 1D arrays, use dense mapping at 180° so the footprint stays 1×L
        (matches 0°) and yields 63 offsets at that angle.
        """
        if k60 == 0:
            out = b
        else:
            # b is already 2D here (ensure_2d_uint8); consider it effectively 1D if any dim is 1
            is_effectively_1d = (b.shape[0] == 1) or (b.shape[1] == 1)
            map_only_nonzero = True
            if is_effectively_1d and k60 == 3:  # 180° in {0,60,120,180,240,300} → k60=3
                map_only_nonzero = False
            out = rotate_array_tri60(b, k60, map_only_nonzero=map_only_nonzero, return_shift=False)
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

    # Perform calls per selected rotation
    per_rotation = {}
    agg_loc_hist= None
    agg_glob_hist = None
    for angle in angles:
        if angle in (0, 180):
            mask = ones_mask
        else:
            # 90/270: if do_smart enabled, use selective mask; else full ones
            mask = quarter_mask if do_smart else ones_mask
        # Call engine with backward-compatibility: prefer 7 args (with local_histogram), fallback to 6 args

        res = eqcorr2d_engine.compute(A_list, B_rot[angle], mask, int(hist), int(report_full), int(False), int(local_histogram))

        # build aggregated histograms over rotations if needed
        if hist:
            if agg_glob_hist is None:
                agg_glob_hist = res[0]
            else:
                agg_glob_hist = agg_glob_hist + res[0]
        if local_histogram:
            if agg_loc_hist is None:
                agg_loc_hist = res[3]
            else:
                agg_loc_hist = agg_loc_hist + res[3]

        # Prepare per-rotation entry save if full report is requested
        if report_full:
            hist_a = res[0]
            full_a = res[1]
            loc_hist = res[3]
            per_rotation[angle] = {
                'hist': hist_a,
                'full': full_a,
                'local_hist': loc_hist,
            }

    return {
        'angles': angles,
        'hist_total': agg_glob_hist,
        'rotations': per_rotation,
        'handle_keys': handle_keys,
        'anti_handle_keys': antihandle_keys,
        'local_hist_total': agg_loc_hist,
    }

def get_worst_match(c_results):
    """Return the worst (highest non-zero) matchtype from a result.
    Supports both the new dict return from wrap_eqcorr2d and the legacy tuple.
    """

    hist = c_results.get('hist_total')
    worst = None

    for matchtype, count in enumerate(hist):
        if count != 0:
            worst = matchtype
    if worst is None:
        print('Warning: no histogram found, returning worst=None')
    return worst

def get_sum_score(c_results, fudge_dg=10):
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
        summe = summe + count * np.exp(fudge_dg * matchtype)
    return summe

def get_seperate_worst_lists(c_results):
    """Return separate lists of worst handle and antihandle identifiers.
    Accepts both new dict and legacy tuple results.
    For the new dict, worst_keys_combos are already keys, not indices.
    """
    worst = get_worst_match(c_results)
    handle_keys = c_results.get('handle_keys')
    antihandle_keys = c_results.get('anti_handle_keys')
    local_hist_total = c_results.get('local_hist_total')
    if worst is None:
        print("Warning: global histogram needed to compute worst list, returning (None,None)")
        return None, None

    if local_hist_total is None:
        print ("Warning: local histogram needet to compute worst list , returning (None,None)")
        return None, None

    worst_slice = local_hist_total[:, :, worst]
    ii, jj = np.where(worst_slice > 0)
    handle_list = [handle_keys[i] for i in ii]
    antihandle_list = [antihandle_keys[j] for j in jj]
    return (handle_list, antihandle_list)

def get_worst_keys_combos(c_results):
    """
    Return a list of (handle_key, antihandle_key) tuples that contributed
    to the global worst histogram bin.

    Relies only on the Python-side 'local_hist_total' 3D array
    of shape (nA, nB, L) and the key lists.
    """
    worst = get_worst_match(c_results)
    handle_keys = c_results.get('handle_keys')
    antihandle_keys = c_results.get('anti_handle_keys')
    local_hist_total = c_results.get('local_hist_total')

    if worst is None:
        print("Warning: global histogram needed to compute worst list, returning None")
        return None
    if local_hist_total is None:
        print("Warning: local histogram needed to compute worst list, returning None")
        return None

    worst_slice = np.asarray(local_hist_total)[:, :, worst]
    ii, jj = np.where(worst_slice > 0)

    combos = [(handle_keys[i], antihandle_keys[j],1) for i, j in zip(ii, jj)]
    return combos

def get_compensated_worst_keys_combos(c_results, connection_graph):
    worst = get_worst_match(c_results)
    handle_keys = c_results['handle_keys']
    anti_keys   = c_results['anti_handle_keys']
    loc = np.asarray(c_results['local_hist_total'])# ja ja chat gpt ensure that data types are always correct

    worst_slice = loc[:, :, worst]  # counts per (i,j) in the worst bin

    # we won't skip anything if it's about matches of 1 or less since they are somehow convoluted in the do smart scheme.
    if worst <=1:
        expected_skips = []
    else:
        expected_skips = connection_graph.get(worst, []) # if it's not in there skip nothing
    skip_counts = Counter(expected_skips)  # multiplicities to skip in this bin. not sure if counter is needed they could be unique already. who knows

    combos = []
    skipped = []
    for i, j in zip(*np.where(worst_slice > 0)):

        pair = (handle_keys[i], anti_keys[j])
        count_hist = int(worst_slice[i, j])
        count_skip = skip_counts.get(pair, 0) # it's either 1 or 0 since connection graph should not have duplicates

        if count_skip > 0:
            skipped.append(pair)

        # Skip only when the skip list covers all occurrences (==), else keep full count
        if count_skip == count_hist: # if both are 1, skip this pair entirely. count_hist might actually be larger than 1.
            continue

        combos.append((pair[0], pair[1], count_hist-count_skip)) # record the difference for bookkeeping
        if count_skip > count_hist:
            raise ValueError(f"Over-subtraction detected for pair {pair}: We have a deeply routed bug if this happens.")
    # sanity check to verify all expected skips were found

    if len(skipped) != len(expected_skips):
        raise RuntimeError(
            f"Warning: some expected skips were not found in the worst pairs. There might be a bug.\n"
            f"Skipped pairs: {skipped}\n"
            f"Expected skips from connection graph: {expected_skips}"
        )

    return combos

def get_similarity_hist(handle_dict, antihandle_dict, mode='square_grid', do_smart=True):
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
                           mode=mode, do_smart=do_smart,
                           hist=True, report_full=False)
    hist_hh = res_hh['hist_total']

    # Compute pairwise stats within the antihandle set
    res_ahah = wrap_eqcorr2d(antihandle_dict, antihandle_dict,
                             mode=mode, do_smart=do_smart,
                             hist=True, report_full=False)
    hist_ahah = res_ahah['hist_total']

    # Sum with safe length alignment
    length = max(len(hist_hh), len(hist_ahah))
    hist_combined = np.zeros(length, dtype=np.int64)
    hist_combined[:len(hist_hh)] += np.asarray(hist_hh, dtype=np.int64)
    hist_combined[:len(hist_ahah)] += np.asarray(hist_ahah, dtype=np.int64)

    # Build self-match correction vector and subtract
    correction = np.zeros(length, dtype=np.int64)
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
