import os, time
import numpy as np
import eqcorr2d
from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming, multirule_precise_hamming, oneshot_hamming_compute,extract_handle_dicts
from crisscross.core_functions.megastructures import Megastructure

def wrap_eqcorr2d(handle_dict, antihandle_dict,
                  rot0=True, rot90=False, rot180=True, rot270=False,
                  hist=True, report_full=False, report_worst=True):
    """takes dicts of arrays (1D or 2D) and runs C ext"""

    def ensure_2d_uint8(arr):
        arr = np.asarray(arr, dtype=np.uint8)
        if arr.ndim == 1:
            arr = arr[np.newaxis, :]  # (L,) -> (1, L)
        elif arr.ndim != 2:
            raise ValueError(f"Array must be 1D or 2D, got shape {arr.shape}")
        if not arr.flags['C_CONTIGUOUS']:
            arr = np.ascontiguousarray(arr)
        return arr

    A_list = [ensure_2d_uint8(a) for a in handle_dict.values()]
    B_list = [ensure_2d_uint8(b) for b in antihandle_dict.values()]

    #  and returns 6 items.
    hist, r0, r90, r180, r270, worst_pairs  = eqcorr2d.compute(
        A_list, B_list,
        int(rot0), int(rot90), int(rot180), int(rot270),
        int(hist), int(report_full), int(report_worst)
    )

    handle_keys= list(handle_dict.keys())
    antihandle_keys= list(antihandle_dict.keys())

    # map original handle keys back to the reported worst combinations


    if report_worst:
        worst_keys_combos = []
        for tubel in worst_pairs:
            handle_index= tubel[0]
            antihandle_index = tubel[1]

            worst_handle_key= handle_keys[handle_index]
            worst_antihandle_key= antihandle_keys[antihandle_index]

            worst_keys_combos.append((worst_handle_key,worst_antihandle_key))
    else:
        worst_keys_combos= None


    return (hist, r0, r90, r180, r270,worst_keys_combos )

def get_worst_match(c_results):
    hist = c_results[0]
    worst = None
    for matchtype, count in enumerate(hist):
        if count != 0:
            worst = matchtype
    return worst

def get_sum_score(c_results,fudge_dg=-10):
    hist = c_results[0]
    summe =0
    for matchtype, count in enumerate(hist):
        summe = summe +count*np.exp(-fudge_dg*matchtype)

    return summe

def get_seperate_worst_lists(c_results):
    worst = c_results[5]
    handle_list =[]
    antihandle_list=[]
    for tuble in worst:
        handle_list.append(tuble[0])
        antihandle_list.append(tuble[1])
    return (handle_list, antihandle_list)


def get_similarity_hist(handle_dict, antihandle_dict,rot0=True, rot90=False, rot180=True, rot270=False):
    res_hh = wrap_eqcorr2d(handle_dict, handle_dict,
                           rot0=rot0, rot90=rot90, rot180=rot180, rot270=rot270,
                           hist=True, report_full=False, report_worst=False)
    hist_hh = res_hh[0]

    res_ahah = wrap_eqcorr2d(antihandle_dict, antihandle_dict,
                             rot0=rot0, rot90=rot90, rot180=rot180, rot270=rot270,
                             hist=True, report_full=False, report_worst=True)
    hist_ahah = res_ahah[0]

    length = max(len(hist_hh), len(hist_ahah))
    hist_combined = np.zeros(length)

    hist_combined[:len(hist_hh)] += hist_hh
    hist_combined[:len(hist_ahah)] += hist_ahah

    correction= np.zeros(length)
    for handle in list(handle_dict.values()):
        self_match  = np.count_nonzero(handle)
        correction[self_match] = correction[self_match]+1


    for antihandle in list(antihandle_dict.values()):
        self_match  = np.count_nonzero(antihandle)
        correction[self_match] = correction[self_match]+1

    corrected_result = hist_combined-correction

    return (corrected_result, None,None, None, None,None )




if __name__ == "__main__":

    # test this on a real example

    megastructure = Megastructure(import_design_file="/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/hash_cad_validation_designs/hexagon/hexagon_design_hashcad_seed.xlsx")
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

