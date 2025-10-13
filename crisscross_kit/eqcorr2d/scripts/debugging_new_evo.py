
if __name__ == '__main__':
    from crisscross.core_functions.slat_design import generate_standard_square_slats
    from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming
    from crisscross.slat_handle_match_evolver import generate_random_slat_handles
    from crisscross.core_functions.megastructures import Megastructure
    from crisscross.slat_handle_match_evolver.handle_evolution import EvolveManager
    import time


    # JUST A TESTING AREA
    test_slat_array, unique_slats_per_layer = generate_standard_square_slats(32)  # standard square
    handle_array = generate_random_slat_handles(test_slat_array, 32)
    megastructure = Megastructure(slat_array=test_slat_array)
    megastructure.assign_assembly_handles(handle_array)

    # megastructure = Megastructure(import_design_file="/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/hash_cad_validation_designs/bird/bird_design_hashcad_seed.xlsx")
    megastructure = Megastructure(import_design_file="/Users/matt/Desktop/Tiny Hexagon Optim.xlsx")
    # megastructure = Megastructure(import_design_file="/Users/matt/Desktop/TEST_PLUS.xlsx")

    # megastructure = Megastructure(import_design_file="C:/Users\Flori\Dropbox\CrissCross\Temporary files\Tiny Hexagon Optim.xlsx")
    print('------')
    t1 = time.time()
    print(multirule_oneshot_hamming(megastructure.generate_slat_occupancy_grid(),megastructure.generate_assembly_handle_grid(),per_layer_check=True, report_worst_slat_combinations=False,request_substitute_risk_score=True))
    t2 = time.time()
    print('------')
    t3 = time.time()
    print(megastructure.get_parasitic_interactions())
    t4 = time.time()
    print('old time:', t2 - t1)
    print('new time:', t4 - t3)

    # evolve_manager =  EvolveManager(megastructure, unique_handle_sequences=64,
    #                                 early_max_valency_stop=0, evolution_population=50,
    #                                 generational_survivors=3,
    #                                 mutation_rate=2,
    #                                 process_count=4,
    #                                 evolution_generations=2000,
    #                                 split_sequence_handles=False,
    #                                 progress_bar_update_iterations=1,
    #                                 log_tracking_directory='/Users/matt/Desktop/delete_me')
    #
    # evolve_manager.run_full_experiment(logging_interval=2)
