if __name__ == '__main__':
    from crisscross.core_functions.slat_design import generate_standard_square_slats
    from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming, \
        multirule_precise_hamming
    from crisscross.slat_handle_match_evolver import generate_random_slat_handles
    from crisscross.slat_handle_match_evolver.handle_evolution import EvolveManager
    from crisscross.core_functions.megastructures import Megastructure

    # JUST A TESTING AREA
    test_slat_array, unique_slats_per_layer = generate_standard_square_slats(32)  # standard square
    handle_array = generate_random_slat_handles(test_slat_array, 32)

    print('Original Results:')
    print(
        multirule_oneshot_hamming(test_slat_array, handle_array, per_layer_check=True, report_worst_slat_combinations=False,
                                  request_substitute_risk_score=True))
    print(multirule_precise_hamming(test_slat_array, handle_array, per_layer_check=True, request_substitute_risk_score=True))

    megastructure = Megastructure(slat_array=test_slat_array)
    megastructure.assign_assembly_handles(handle_array)

    evolve_manager =  EvolveManager(megastructure, unique_handle_sequences=64,
                                    early_worst_match_stop=2, evolution_population=50,
                                    generational_survivors=3,
                                    mutation_rate=2,
                                    process_count=4,
                                    evolution_generations=2000,
                                    split_sequence_handles=False,
                                    progress_bar_update_iterations=1,
                                    log_tracking_directory='/Users/matt/Desktop/delete_me')

    evolve_manager.run_full_experiment(logging_interval=5)
    ergebnüsse = evolve_manager.handle_array # this is the best array result

    print('New Results:')
    print(multirule_oneshot_hamming(test_slat_array, ergebnüsse, per_layer_check=True, report_worst_slat_combinations=False,
                                    request_substitute_risk_score=True))
    print(multirule_precise_hamming(test_slat_array, ergebnüsse, per_layer_check=True, request_substitute_risk_score=True))
