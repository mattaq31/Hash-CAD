from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming, extract_handle_dicts
from crisscross.core_functions.megastructures import Megastructure
from eqcorr2d.eqcorr2d_interface import wrap_eqcorr2d, get_similarity_hist, get_sum_score, get_worst_match, get_seperate_worst_lists

# example integration
megastructure = Megastructure(
    import_design_file="C:/Users\Flori\Dropbox\CrissCross\Papers\hash_cad\design_library\hexagon\hexagon_design_hashcad_seed_crap.xlsx")
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
