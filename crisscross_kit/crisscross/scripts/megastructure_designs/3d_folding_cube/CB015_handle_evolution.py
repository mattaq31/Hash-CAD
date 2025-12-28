if __name__ == '__main__':
    from crisscross.slat_handle_match_evolver.handle_evolution import EvolveManager
    from crisscross.core_functions.megastructures import Megastructure, get_slat_key

    # corner_file = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Crisscross Designs/CB015_3d_cube/3DCorner_V1_with_dummy_slats.xlsx'
    corner_file = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Crisscross Designs/CB015_3d_cube/3DCorner_V2_no_handles.xlsx'

    megastructure = Megastructure(import_design_file=corner_file)

    linked_handles = {}

    # REMOVE TWO SLATS FROM THE TOP AND BOTTOM OF THE HINGE REGIONS
    for s1 in range(1, 14 + 1):
        for s2 in range(15, 28 + 1):
            t1_pos = megastructure.slats[get_slat_key(3, s1)].slat_position_to_coordinate[s2 + 3]
            t2_pos = megastructure.slats[get_slat_key(3, s2)].slat_position_to_coordinate[32 - s1]
            linked_handles[(3, 'top', t1_pos)] = (3, 'bottom', t2_pos)  # layer, slat, handle index

    # step 1: shave off top layer from megastructure
    # step 2: run through the slats that are 'long' and make a new slat combining the two
    
    evolve_manager = EvolveManager(megastructure,
                                   unique_handle_sequences=64,
                                   early_max_valency_stop=1, evolution_population=50,
                                   generational_survivors=3,
                                   mutation_rate=2,
                                   process_count=4,
                                   random_seed=12,
                                   evolution_generations=20000,
                                   split_sequence_handles=False,
                                   progress_bar_update_iterations=10,
                                   repeating_unit_constraints=linked_handles,
                                   log_tracking_directory='/Users/matt/Desktop/CB015_v2_with_correct_links')

    evolve_manager.run_full_experiment(logging_interval=10)
