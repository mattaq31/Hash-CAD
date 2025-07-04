
if __name__ == '__main__':
    from crisscross.core_functions.megastructures import Megastructure
    from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming, \
        multirule_precise_hamming
    from crisscross.assembly_handle_optimization.handle_evolution import EvolveManager

    # JUST A TESTING AREA
    test_file = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/hash_cad_validation_designs/sunflower/sunflower_design_hashcad_seed.xlsx'

    megastructure = Megastructure(import_design_file=test_file)

    slat_array = megastructure.generate_slat_occupancy_grid()

    handle_array = megastructure.generate_assembly_handle_grid()

    print('Original Results:')
    print(
        multirule_oneshot_hamming(slat_array, handle_array, per_layer_check=True, report_worst_slat_combinations=False,
                                  request_substitute_risk_score=True))
    print(multirule_precise_hamming(slat_array, handle_array, per_layer_check=True, request_substitute_risk_score=True))


    evolve_manager =  EvolveManager(slat_array, unique_handle_sequences=64,
                                    early_hamming_stop=30, evolution_population=1,
                                    generational_survivors=1,
                                    mutation_rate=2000,
                                    process_count=1,
                                    evolution_generations=4,
                                    split_sequence_handles=True,
                                    sequence_split_factor=4,
                                    progress_bar_update_iterations=2,
                                    log_tracking_directory='/Users/matt/Desktop/test')

    evolve_manager.run_full_experiment(logging_interval=1)
    ergebnüsse = evolve_manager.handle_array # this is the best array result

    print('New Results:')
    print(multirule_oneshot_hamming(slat_array, ergebnüsse, per_layer_check=True, report_worst_slat_combinations=False,
                                    request_substitute_risk_score=True))
    print(multirule_precise_hamming(slat_array, ergebnüsse, per_layer_check=True, request_substitute_risk_score=True))
