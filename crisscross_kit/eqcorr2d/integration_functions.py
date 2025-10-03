import numpy as np
from . import eqcorr2d_engine
from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming, multirule_precise_hamming, oneshot_hamming_compute,extract_handle_dicts
from crisscross.core_functions.megastructures import Megastructure

def wrap_eqcorr2d(handle_dict, antihandle_dict,
                  mode='classic',
                  hist=True, report_full=False, report_worst=True, do_smart=False):
    """Compute eqcorr2d; return a single structured dict keyed by rotation.

    Design goals:
    - Keep the C layer simple (always computes for "rot0" orientation of inputs).
    - Handle rotations in Python by pre-rotating B for each requested angle.
    - Make the Python return value easy to consume and extend: a single dict
      with per-rotation entries under result['rotations'] and global
      aggregates at the top level.

    do_smart behavior (Python-side approximation):
    - Always compute 0° and 180° when requested.
    - For 90° and 270°: if do_smart is True, compute them only when at least
      one array in A_list or B_list is truly 2D (both dims >= 2). This is a
      coarse approximation of the previous per-pair smart rule.

    Return structure (dictionary):
    {
      'angles': [list of angles actually computed in this call],
      'hist_total': np.ndarray or None,  # sum across angles if hist=True
      'rotations': {
          0:   {'hist': np.ndarray|None, 'full': list|None,
                'worst_pairs_idx': list|None, 'worst_pairs_keys': list|None},
          90:  {...},
          180: {...},
          270: {...}
      },
      'worst_keys_combos': list|None  # globally worst (handle_key, antihandle_key) pairs
    }
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
        elif k60 == 3:
            # 180° is equivalent to np.rot90 with k=2 on square grids
            out = np.rot90(b, k=2)
        else:
            raise NotImplementedError("rot60_py for 60/120/240/300 degrees not implemented yet")
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
    B_rot = { }
    for angle in angles:
        if mode in ('classic', 'square_grid'):
            k = {0:0, 90:1, 180:2, 270:3}.get(angle, None)
            if k is None:
                # shouldn't happen in these modes
                raise ValueError(f"Unsupported angle {angle} for mode {mode}")
            B_rot[angle] = [rot90_py(b, k) for b in B_list]
        else:
            # triangle_grid uses 60° steps; currently only 0 and 180 (k60=0 or 3) are implemented
            k60_map = {0:0, 60:1, 120:2, 180:3, 240:4, 300:5}
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
        res = eqcorr2d.compute(A_list, B_rot[angle], mask, int(hist), int(report_full), int(report_worst))
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



#Do not use this. It would only work if all 1D slats are fully occupied with handles and antihandles
def compensate_do_smart(hist,handle_dict, antihandle_dict,standart_slat_lenght=32,libraray_length=64):
    #extract values from dicts
    handles = list(handle_dict.values())
    antihandles = list(antihandle_dict.values())
    #count 1D and 2D handles in a loop
    count_1D_handles =0
    count_2D_handles =0
    for handle in handles:
        if handle.shape[0]==1:
            count_1D_handles = count_1D_handles+1
        else:
            count_2D_handles = count_2D_handles+1
    #count 1D and 2D antihandles in a loop
    count_1D_antihandles =0
    count_2D_antihandles =0
    for antihandle in antihandles:
        if antihandle.shape[0]==1:
            count_1D_antihandles = count_1D_antihandles+1
        else:
            count_2D_antihandles = count_2D_antihandles+1
    #calculate number of combinations not tested by do_smart
    not_tested_combinations = count_1D_handles*count_1D_antihandles*2 # times 2 for 90 and 270
    left_out_array_lenght=(standart_slat_lenght+1-1)*(standart_slat_lenght+1-1) # this is number of entries of the result arrays not computed
    all_left_out_entries = not_tested_combinations*left_out_array_lenght
    #now calculate expected distribution of these combinations. since the dimension is only 1D of each we can eighter have a matchtype 1 ore 0.
    # the probability for a matchtype 0 is 1/libraray_length
    p0 = 1/libraray_length
    hit1= all_left_out_entries*p0
    hit0= all_left_out_entries*(1-p0)
    #now add these to the histogram
    corrected_hist = hist.copy()
    corrected_hist[0] = corrected_hist[0]+int(hit0)
    corrected_hist[1] = corrected_hist[1]+int(hit1)

    return corrected_hist


def get_similarity_hist(handle_dict, antihandle_dict, mode='square_grid'):
    """Compute a combined similarity histogram for handles and antihandles.
    Returns a dict aligned with wrap_eqcorr2d's new return format, with only
    'hist_total' populated. Per-rotation details are not computed here.
    """
    res_hh = wrap_eqcorr2d(handle_dict, handle_dict,
                           mode=mode,
                           hist=True, report_full=False, report_worst=False)
    hist_hh = res_hh['hist_total']

    res_ahah = wrap_eqcorr2d(antihandle_dict, antihandle_dict,
                             mode=mode,
                             hist=True, report_full=False, report_worst=True)
    hist_ahah = res_ahah['hist_total']

    length = max(len(hist_hh), len(hist_ahah))
    hist_combined = np.zeros(length)

    hist_combined[:len(hist_hh)] += hist_hh
    hist_combined[:len(hist_ahah)] += hist_ahah

    correction = np.zeros(length)
    for handle in list(handle_dict.values()):
        self_match = np.count_nonzero(handle)
        correction[self_match] = correction[self_match] + 1

    for antihandle in list(antihandle_dict.values()):
        self_match = np.count_nonzero(antihandle)
        correction[self_match] = correction[self_match] + 1

    corrected_result = hist_combined - correction

    return {
        'angles': [],
        'hist_total': corrected_result,
        'rotations': {},
        'worst_keys_combos': None,
    }




if __name__ == "__main__":

    # example integration

    megastructure = Megastructure(import_design_file="C:/Users\Flori\Dropbox\CrissCross\Papers\hash_cad\design_library\hexagon\hexagon_design_hashcad_seed.xlsx")
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


    mean_score = sum_score/(len(handle_slats)*len(antihandle_slats)) # this one seems to be the smarter choice
    mean_score_old = mean_score/126

    sim_hist = get_similarity_hist(handle_slats, antihandle_slats)

    worst_sim_match = get_worst_match(sim_hist)
