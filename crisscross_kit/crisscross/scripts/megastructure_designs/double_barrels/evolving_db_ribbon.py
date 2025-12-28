if __name__ == '__main__':
    from crisscross.slat_handle_match_evolver.handle_evolution import EvolveManager
    from crisscross.core_functions.megastructures import Megastructure, get_slat_key
    import os
    import pandas as pd

    design_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Crisscross Designs/MAD DB Ribbon/design'
    design_file = 'design_random_handles.xlsx'
    design_file_evolved = 'design_evolved_handles.xlsx'
    evo_folder = os.path.join(design_folder, 'handle_evolution')
    run_evo = True

    if run_evo:
        megastructure = Megastructure(import_design_file=os.path.join(design_folder, design_file))
    else:
        megastructure = Megastructure(import_design_file=os.path.join(design_folder, design_file_evolved))

    # linking repeating unit handles
    linked_handles = {}
    for iter, slat_id in enumerate(range(33, 49)):
        for end_handle_point in range(17, 33):
            if iter % 2 != 0:
                end_handle_point = end_handle_point - 16
            t1_pos = megastructure.slats[get_slat_key(2, slat_id)].slat_position_to_coordinate[end_handle_point]
            t2_pos = megastructure.slats[get_slat_key(2, 49 + iter)].slat_position_to_coordinate[end_handle_point]
            linked_handles[(2, 'top', t1_pos)] = (2, 'top', t2_pos)  # layer, slat, handle index

    for iter, slat_id in enumerate(range(16, 0, -1)):
        for end_handle_point in range(9, 25):
            t1_pos = megastructure.slats[get_slat_key(1, slat_id)].slat_position_to_coordinate[end_handle_point]

            if iter % 2 == 0:
                t2_pos = megastructure.slats[get_slat_key(1, 24 - int(iter/2))].slat_position_to_coordinate[end_handle_point-8]
            else:
                t2_pos = megastructure.slats[get_slat_key(1, 24 - int(iter/2))].slat_position_to_coordinate[41 - end_handle_point]

            linked_handles[(1, 'top', t1_pos)] = (1, 'top', t2_pos)  # layer, slat, handle index

    if run_evo:
        evolve_manager = EvolveManager(megastructure,
                                       unique_handle_sequences=64,
                                       early_max_valency_stop=1, evolution_population=50,
                                       generational_survivors=1,
                                       mutation_rate=1,
                                       process_count=6,
                                       random_seed=8,
                                       evolution_generations=50,
                                       split_sequence_handles=False,
                                       mutation_type_probabilities=(0.0725, 0.0725, 0.85),
                                       progress_bar_update_iterations=10,
                                       repeating_unit_constraints=linked_handles,
                                       log_tracking_directory=evo_folder)

        evolve_manager.run_full_experiment(logging_interval=10, suppress_handle_array_export=True)

        # only save final array
        writer = pd.ExcelWriter(os.path.join(evo_folder, f'best_handle_array_generation_{evolve_manager.current_generation}.xlsx'), engine='xlsxwriter')

        # prints out handle dataframes in standard format
        for layer_index in range(evolve_manager.handle_array.shape[-1]):
            df = pd.DataFrame(evolve_manager.handle_array[..., layer_index])
            df.to_excel(writer, sheet_name=f'handle_interface_{layer_index + 1}', index=False, header=False)
            # Apply conditional formatting for easy color-based identification
            writer.sheets[f'handle_interface_{layer_index + 1}'].conditional_format(0, 0, df.shape[0],
                                                                                    df.shape[1] - 1,
                                                                                    evolve_manager.excel_conditional_formatting)
        writer.close()

        # also save the design with punched out handles
        megastructure.assign_assembly_handles(evolve_manager.handle_array, suppress_warnings=True)

    pattern_reject_h2 = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32]
    pattern_reject_h5 = [1, 3, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 29, 31]

    slat_array = megastructure.generate_slat_occupancy_grid()

    for slat_index, slat_id in enumerate(range(17, 33)):
        slat_name = 'layer3-slat%s' % slat_id
        input_slat = megastructure.slats[slat_name]

        for handle in pattern_reject_h2:
            # first knockout DB handles
            input_slat.remove_handle(handle, 2)

            # next knockout opposing slat handles too (both top and bottom)
            handle_coord = input_slat.slat_position_to_coordinate[handle]

            opposing_slat_id_bottom = slat_array[handle_coord[0], handle_coord[1], input_slat.layer - 2]
            opposing_slat_bottom = megastructure.slats[f'layer{input_slat.layer - 1}-slat{opposing_slat_id_bottom}']
            opposing_handle = opposing_slat_bottom.slat_coordinate_to_position[handle_coord]

            opposing_slat_bottom.remove_handle(opposing_handle, 5)

            if opposing_slat_id_bottom < 49:
                linked_slat_bottom = megastructure.slats[f'layer{input_slat.layer - 1}-slat{opposing_slat_id_bottom + 16}']
                linked_slat_bottom.remove_handle(opposing_handle, 5)

        for handle in pattern_reject_h5:
            # first knockout DB handles
            input_slat.remove_handle(handle, 5)

            # next knockout opposing slat handles too (both top and bottom)
            handle_coord = input_slat.slat_position_to_coordinate[handle]

            opposing_slat_id_top = slat_array[handle_coord[0], handle_coord[1], input_slat.layer]

            opposing_slat_top = megastructure.slats[f'layer{input_slat.layer + 1}-slat{opposing_slat_id_top}']
            opposing_handle = opposing_slat_top.slat_coordinate_to_position[handle_coord]
            opposing_slat_top.remove_handle(opposing_handle, 2)


    # also need to enforce handle 58 on positions 2 and 30 in the repeating units (in specific places)
    repeating_unit_slats = {3: list(range(17, 33)), 2: list(range(49, 65)) + list(range(33, 49))} # key: layer, values: IDs

    # don't apply handle 58 in these specific locations (to ensure valency remains low)
    reject_list = {2: {2:[50, 52, 54, 56, 33, 34, 35, 36, 37, 39, 41, 43, 45, 47, 38, 40],
                       30:[52, 58, 60, 64, 53, 57, 61, 63, 34, 36, 38, 40, 42, 44, 45, 46, 47, 48, 37, 41]},
                   3: {2:[17, 18, 19, 22, 23, 24, 27, 30], 30:[25, 27, 29, 31]}}

    force_id = 58
    for layer, slats in repeating_unit_slats.items():
        for slat_id in slats:
            slat_name = 'layer%s-slat%s' % (layer, slat_id)

            target_slat = megastructure.slats[slat_name]

            for position in [5]:
                for enforce_pos in [2, 30]:

                    if slat_id in reject_list[layer][enforce_pos]: # skip the reject list
                        continue

                    if enforce_pos not in target_slat.H5_handles: # skip if no handle was there to begin with
                        continue

                    handle_id = target_slat.H5_handles[enforce_pos]

                    if handle_id != force_id and handle_id != 0:
                        handle_coord = target_slat.slat_position_to_coordinate[enforce_pos]
                        target_slat.set_placeholder_handle(enforce_pos, position, 'ASSEMBLY_HANDLE', force_id, 'N/A', suppress_warnings=True)

                        opposing_slat_id_top = slat_array[handle_coord[0], handle_coord[1], target_slat.layer]
                        if opposing_slat_id_top != 0:
                            opposing_slat_top = megastructure.slats[f'layer{target_slat.layer + 1}-slat{opposing_slat_id_top}']
                            opposing_handle = opposing_slat_top.slat_coordinate_to_position[handle_coord]
                            opposing_slat_top.remove_handle(opposing_handle, 2)

    if run_evo:
        megastructure.export_design('design_evolved_handles_linked.xlsx', design_folder)
    else:
        megastructure.export_design('design_evolved_new_links.xlsx', design_folder)


