if __name__ == '__main__':
    from crisscross.core_functions.slat_design import generate_standard_square_slats
    from crisscross.slat_handle_match_evolver import generate_random_slat_handles
    from crisscross.slat_handle_match_evolver.handle_evolution import EvolveManager
    from crisscross.core_functions.megastructures import Megastructure

    # JUST A TESTING AREA
    slat_count = 32
    test_slat_array, unique_slats_per_layer = generate_standard_square_slats(slat_count)  # standard square
    handle_array = generate_random_slat_handles(test_slat_array, 64)

    # megastructure = Megastructure(slat_array=test_slat_array)
    # megastructure.assign_assembly_handles(handle_array)


    megastructure = Megastructure(import_design_file='/Users/matt/Desktop/test_evolve.xlsx')

    print('Original Results:')
    print(megastructure.get_parasitic_interactions())

    evolve_manager =  EvolveManager(megastructure, unique_handle_sequences=64,
                                    early_max_valency_stop=1, evolution_population=50,
                                    generational_survivors=1,
                                    mutation_rate=10,
                                    process_count=6,
                                    evolution_generations=100,
                                    split_sequence_handles=False,
                                    progress_bar_update_iterations=1,
                                    update_scope='all',
                                    log_tracking_directory='/Users/matt/Desktop/delete_me')

    evolve_manager.run_full_experiment(logging_interval=5)
    megastructure.assign_assembly_handles(evolve_manager.handle_array)

    print('New Results:')
    print(megastructure.get_parasitic_interactions())
