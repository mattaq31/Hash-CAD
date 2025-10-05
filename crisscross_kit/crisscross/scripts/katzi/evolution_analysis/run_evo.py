from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming, multirule_precise_hamming, oneshot_hamming_compute,extract_handle_dicts
from crisscross.slat_handle_match_evolver import generate_random_slat_handles
from crisscross.slat_handle_match_evolver.handle_evolution import EvolveManager
from crisscross.core_functions.megastructures import Megastructure
import numpy as np

def perfect_fake_square():
    """
    Return a (size x size x 1) int array where each row r has:
      - left half filled with 2*r + 1
      - right half filled with 2*r + 2
    For size=32: rows are (1,2), (3,4), ..., (63,64).
    """
    size = 32
    if size % 2 != 0:
        raise ValueError("size must be even so rows split cleanly in half.")
    rows = np.arange(size)[:, None]          # shape (size, 1)
    cols = np.arange(size)[None, :]          # shape (1, size)
    half = size // 2
    left_vals  = 2 * rows + 1                # (size, 1)
    right_vals = left_vals + 1               # (size, 1)
    arr2d = np.where(cols < half, left_vals, right_vals).astype(np.int64)  # (size, size)
    return arr2d[..., None]                  # (size, size, 1)

if __name__ == '__main__':
    # use this to generate a quick square
    #test_slat_array, unique_slats_per_layer = generate_standard_square_slats(32)  # standard square
    #handle_array = generate_random_slat_handles(test_slat_array, 32)

    # use this to read a specific design from file
    megastructure = Megastructure(import_design_file="C:/Users\Flori\Dropbox\CrissCross\Papers\hash_cad\design_library/recycling/recycling_design_hashcad_seed.xlsx")
    slat_array = megastructure.generate_slat_occupancy_grid()
    #handle_array = megastructure.generate_assembly_handle_grid()
    hotstart = None
    #hotstart = rhl("D:\Wyss_experiments\Evolution_analysis\evo_run_hexagon_2/best_handle_array_generation_24000.xlsx")
    #hotstart=perfect_fake_square()
    #print('Original metrics from file:')
    #print(
    #    multirule_oneshot_hamming(test_slat_array, handle_array, per_layer_check=True, report_worst_slat_combinations=False,
    #                              request_substitute_risk_score=True))
    #print(multirule_precise_hamming(test_slat_array, handle_array, per_layer_check=True, request_substitute_risk_score=True))


    evolve_manager =  EvolveManager(slat_array, unique_handle_sequences=64,
                                    seed_handle_array=hotstart,
                                    early_hamming_stop=32, evolution_population=50,
                                    mutation_type_probabilities=(0.425, 0.425, 0.15),
                                    generational_survivors=5,
                                    mutation_rate=2,
                                    process_count=8,
                                    evolution_generations=1000,
                                    split_sequence_handles=False,
                                    progress_bar_update_iterations=1,
                                    random_seed=8,
                                    log_tracking_directory='D:\Wyss_experiments\Evolution_analysis/thalahon')

    evolve_manager.run_full_experiment(logging_interval=1)
    ergebnüsse = evolve_manager.handle_array # this is the best array result

    print('New Results:')
    print(multirule_oneshot_hamming(slat_array, ergebnüsse, per_layer_check=True, report_worst_slat_combinations=False,
                                    request_substitute_risk_score=True))
    print(multirule_precise_hamming(slat_array, ergebnüsse, per_layer_check=True, request_substitute_risk_score=True))
