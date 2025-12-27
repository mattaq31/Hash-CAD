if __name__ == '__main__':
    from crisscross.slat_handle_match_evolver.handle_evolution import EvolveManager
    from crisscross.core_functions.megastructures import Megastructure, get_slat_key
    import os
    import pandas as pd

    design_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/hash_cad_validation_designs/2d_hc_ribbon/'
    design_file = 'S24_paper_ribbon.xlsx'
    design_file_with_extra_slats = 'S24_paper_ribbon_with_all_handles_covered.xlsx'
    evo_folder = os.path.join(design_folder, 'evolution_log')

    megastructure = Megastructure(import_design_file=os.path.join(design_folder, design_file_with_extra_slats))

    linked_handles = {}

    # start linking handles
    for slat_id in range(1, 9):
        for handle_offset in range(8 - slat_id, -1, -1):
            t1_pos = megastructure.slats[get_slat_key(1, slat_id)].slat_position_to_coordinate[32 - handle_offset]
            t2_pos = megastructure.slats[get_slat_key(1, slat_id + 16)].slat_position_to_coordinate[32 - handle_offset]
            linked_handles[(1, 'top', t1_pos)] = (1, 'top', t2_pos)  # layer, slat, handle index

    for iter, slat_id in enumerate(range(56, 63)):
        for end_handle_point in range(23 - iter, 16, -1):
            t1_pos = megastructure.slats[get_slat_key(1, slat_id)].slat_position_to_coordinate[end_handle_point]
            t2_pos = megastructure.slats[get_slat_key(1, 16 - iter)].slat_position_to_coordinate[end_handle_point]
            linked_handles[(1, 'top', t1_pos)] = (1, 'top', t2_pos)  # layer, slat, handle index

    for iter, slat_id in enumerate(range(1, 9)):
        for end_handle_point in range(9 + iter, 17):
            t1_pos = megastructure.slats[get_slat_key(1, slat_id)].slat_position_to_coordinate[end_handle_point]
            t2_pos = megastructure.slats[get_slat_key(1, 48 + iter)].slat_position_to_coordinate[end_handle_point]
            linked_handles[(1, 'top', t1_pos)] = (1, 'top', t2_pos)  # layer, slat, handle index

    for iter, slat_id in enumerate(range(10, 17)):
        for end_handle_point in range(1, 2 + iter):
            t1_pos = megastructure.slats[get_slat_key(1, slat_id)].slat_position_to_coordinate[end_handle_point]
            t2_pos = megastructure.slats[get_slat_key(1, 25 + iter)].slat_position_to_coordinate[end_handle_point]
            linked_handles[(1, 'top', t1_pos)] = (1, 'top', t2_pos)  # layer, slat, handle index

    for iter, slat_id in enumerate(range(1, 10)):
        for end_handle_point in range(1, 9 + iter):
            t1_pos = megastructure.slats[get_slat_key(1, slat_id)].slat_position_to_coordinate[end_handle_point]
            t2_pos = megastructure.slats[get_slat_key(1, 32 + iter)].slat_position_to_coordinate[end_handle_point]
            linked_handles[(1, 'top', t1_pos)] = (1, 'top', t2_pos)  # layer, slat, handle index

    for iter, slat_id in enumerate(range(10, 17)):
        for end_handle_point in range(2 + iter, 17):
            t1_pos = megastructure.slats[get_slat_key(1, slat_id)].slat_position_to_coordinate[end_handle_point]
            t2_pos = megastructure.slats[get_slat_key(1, 41 + iter)].slat_position_to_coordinate[end_handle_point]
            linked_handles[(1, 'top', t1_pos)] = (1, 'top', t2_pos)  # layer, slat, handle index


    evolve_manager = EvolveManager(megastructure,
                                   unique_handle_sequences=64,
                                   early_max_valency_stop=1, evolution_population=50,
                                   generational_survivors=1,
                                   mutation_rate=1,
                                   process_count=6,
                                   random_seed=8,
                                   evolution_generations=1000,
                                   split_sequence_handles=False,
                                   mutation_type_probabilities=(0.0725, 0.0725, 0.85),
                                   progress_bar_update_iterations=10,
                                   repeating_unit_constraints={'link_handles': linked_handles},
                                   log_tracking_directory=evo_folder)

    evolve_manager.run_full_experiment(logging_interval=10, suppress_handle_array_export=True)

    # only save final array
    writer = pd.ExcelWriter(
        os.path.join(evo_folder, f'best_handle_array_generation_{evolve_manager.current_generation}.xlsx'),
        engine='xlsxwriter')

    # prints out handle dataframes in standard format
    for layer_index in range(evolve_manager.handle_array.shape[-1]):
        df = pd.DataFrame(evolve_manager.handle_array[..., layer_index])
        df.to_excel(writer, sheet_name=f'handle_interface_{layer_index + 1}', index=False, header=False)
        # Apply conditional formatting for easy color-based identification
        writer.sheets[f'handle_interface_{layer_index + 1}'].conditional_format(0, 0, df.shape[0],
                                                                                df.shape[1] - 1,
                                                                                evolve_manager.excel_conditional_formatting)
    writer.close()
