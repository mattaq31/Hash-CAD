

# TODO: This script needs to be updated to the new syntax system
if __name__ == '__main__':
    from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming
    from crisscross.slat_handle_match_evolver import generate_random_slat_handles
    from crisscross.slat_handle_match_evolver.handle_evolution import EvolveManager
    from crisscross.core_functions.megastructures import Megastructure, get_slat_key
    import pandas as pd
    import os

    repeating_unit_edited_file = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/hash_cad_validation_designs/pointy_ribbon/pointy_ribbon_seed_and_repeating_unit_combined_no_handles.xlsx'

    # JUST A TESTING AREA
    megastructure = Megastructure(import_design_file=repeating_unit_edited_file)

    linked_handles = {}

    handle_links = 0
    for s1, s2 in zip(range(41, 57), range(1, 17)):
        handle_links += 1
        for h in range(1, handle_links + 1):
            t1_pos = megastructure.slats[get_slat_key(1, s1)].slat_position_to_coordinate[33-h]
            t2_pos = megastructure.slats[get_slat_key(1, s2)].slat_position_to_coordinate[33-h]
            linked_handles[(1, 'top', t1_pos)] = (1, 'top', t2_pos) # layer, slat, handle index

    handle_links = 0
    for s1, s2 in zip(range(41, 57), range(1, 17)):
        handle_links += 1
        for h in range(1, ((handle_links-1)// 4) + 2):
            t1_pos = megastructure.slats[get_slat_key(1, s1)].slat_position_to_coordinate[h]
            t2_pos = megastructure.slats[get_slat_key(1, s2)].slat_position_to_coordinate[h]
            linked_handles[(1,'top', t1_pos)] = (1,'top', t2_pos) # layer, slat, handle index

    handle_links = 16
    for s1, s2 in zip(range(53, 56), range(33, 36)):
        handle_links -= 4
        for h in range(1, handle_links + 1):
            t1_pos = megastructure.slats[get_slat_key(2, s1)].slat_position_to_coordinate[33-h]
            t2_pos = megastructure.slats[get_slat_key(2, s2)].slat_position_to_coordinate[33-h]
            linked_handles[(2, 'bottom', t1_pos)] = (2, 'bottom', t2_pos) # layer, slat, handle index

    handle_links = 0
    for s1, s2 in zip(range(41, 53), range(1, 13)):
        handle_links += 1
        for h in range(1, ((handle_links-1)// 4) + 6):
            t1_pos = megastructure.slats[get_slat_key(2, s1)].slat_position_to_coordinate[h]
            t2_pos = megastructure.slats[get_slat_key(2, s2)].slat_position_to_coordinate[h]
            linked_handles[(2, 'bottom', t1_pos)] = (2, 'bottom', t2_pos) # layer, slat, handle index

    transplant_slats = {}

    base_range = [40, 39, 38, 37]
    handle_links = 0
    for s1 in range(17, 33):
        handle_links += 1
        multiplier = (handle_links-1) // 4
        for h in range(1, multiplier + 2):
            t1_pos = megastructure.slats[get_slat_key(2, s1)].slat_position_to_coordinate[h]
            t2_pos = megastructure.slats[get_slat_key(1, base_range[h-1])].slat_position_to_coordinate[handle_links - 4 * (h-1)]
            transplant_slats[(2, 'bottom', t1_pos)] = (1, 'bottom', t2_pos) # layer, slat, handle index

    for _ in range(1000):
        handle_array = generate_random_slat_handles(megastructure.generate_slat_occupancy_grid(), 64, transplant_slats, linked_handles)
        # megastructure.assign_assembly_handles(handle_array)
        print('Original Results:')
        results = multirule_oneshot_hamming(megastructure.generate_slat_occupancy_grid(), handle_array, per_layer_check=True, report_worst_slat_combinations=False, request_substitute_risk_score=True)
        print(results)
        if results['Universal'] == 26:
            excel_conditional_formatting = {'type': '3_color_scale',
                                            'criteria': '<>',
                                            'min_color': "#63BE7B",  # Green
                                            'mid_color': "#FFEB84",  # Yellow
                                            'max_color': "#F8696B",  # Red
                                            'value': 0}
            writer = pd.ExcelWriter(
                os.path.join('/Users/matt/Desktop', f'26_array.xlsx'), engine='xlsxwriter')

            # prints out slat dataframes in standard format
            for layer_index in range(handle_array.shape[-1]):
                df = pd.DataFrame(handle_array[..., layer_index])
                df.to_excel(writer, sheet_name=f'handle_interface_{layer_index + 1}', index=False, header=False)
                # Apply conditional formatting for easy color-based identification
                writer.sheets[f'handle_interface_{layer_index + 1}'].conditional_format(0, 0, df.shape[0],
                                                                                        df.shape[1] - 1,
                                                                                        excel_conditional_formatting)
            writer.close()
            break

    evolve_manager =  EvolveManager(megastructure.generate_slat_occupancy_grid(),
                                    unique_handle_sequences=64,
                                    early_hamming_stop=31, evolution_population=50,
                                    generational_survivors=3,
                                    mutation_rate=2,
                                    process_count=8,
                                    random_seed=12,
                                    evolution_generations=2000,
                                    split_sequence_handles=False,
                                    progress_bar_update_iterations=2,
                                    repeating_unit_constraints={'transplant_handles': transplant_slats, 'link_handles': linked_handles},
                                    log_tracking_directory='/Users/matt/Desktop/ribbon_evo_run')

    evolve_manager.run_full_experiment(logging_interval=1)
