from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming, multirule_precise_hamming
from crisscross.assembly_handle_optimization import generate_random_slat_handles
from crisscross.assembly_handle_optimization.handle_evolution import EvolveManager

if __name__ == '__main__':
    # JUST A TESTING AREA
    test_slat_array, unique_slats_per_layer = generate_standard_square_slats(32)  # standard square
    handle_array = generate_random_slat_handles(test_slat_array, 32)

    print('Original Results:')
    print(
        multirule_oneshot_hamming(test_slat_array, handle_array, per_layer_check=True, report_worst_slat_combinations=False,
                                  request_substitute_risk_score=True))
    print(multirule_precise_hamming(test_slat_array, handle_array, per_layer_check=True, request_substitute_risk_score=True))


    evolve_manager =  EvolveManager(test_slat_array, unique_handle_sequences=32,
                                    early_hamming_stop=30, evolution_population=10,
                                    generational_survivors=2,
                                    mutation_rate=2,
                                    process_count=4,
                                    evolution_generations=100,
                                    split_sequence_handles=False,
                                    progress_bar_update_iterations=2,
                                    log_tracking_directory='/Users/matt/Desktop')

    evolve_manager.run_full_experiment(logging_interval=1)
    ergebnüsse = evolve_manager.handle_array # this is the best array result

    print('New Results:')
    print(multirule_oneshot_hamming(test_slat_array, ergebnüsse, per_layer_check=True, report_worst_slat_combinations=False,
                                    request_substitute_risk_score=True))
    print(multirule_precise_hamming(test_slat_array, ergebnüsse, per_layer_check=True, request_substitute_risk_score=True))
