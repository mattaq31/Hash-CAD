import os
import numpy as np
import pandas as pd
from crisscross.core_functions.plate_handling import read_dna_plate_mapping
from crisscross.helper_functions.plate_maps import (slat_core, plate_folder, crisscross_handle_plates,
                                                    seed_plug_plate_corner, plate96, sanitize_plate_map)
from collections import defaultdict


def extract_h5_staples(handle_ids, core_slat_plate, crisscross_plates, cargo_plate=None, cargo_name_dict=None, cargo_bearing=False):

    staple_selection = []
    for i, handle in enumerate(handle_ids):
        if handle == -1:
            sel_plate = core_slat_plate
            core_name = 'slatcore-%s-h5ctrl' % (33 + i)
            sel_location = sel_plate[sel_plate['name'].str.contains(core_name)]
            staple_selection.append(
                [sanitize_plate_map(slat_core), sel_location['well'].values[0], sel_location['sequence'].values[0]])
        elif cargo_bearing:
            sel_location = cargo_plate[cargo_plate['Name'] == f'{cargo_name_dict[handle]}_h5_cargo_handle_{i + 1}']
            staple_selection.append(['cargo_plate', sel_location['WellPosition'].values[0], sel_location['Sequence'].values[0]])
        else:
            sel_plate = crisscross_plates[i // 12][0]
            sel_location = sel_plate[sel_plate['description'].str.contains('n%s_k%s' % (i, handle))]
            staple_selection.append(
                [sanitize_plate_map(crisscross_plates[i // 12][1]), sel_location['well'].values[0], sel_location['sequence'].values[0]])
    return staple_selection


def extract_cargo_staples(cargo_val, slat_pos_id, cargo_name_dict, core_slat_plate, cargo_plate, seed_here=False, seed_plug_plate=None, y_position=None):

    if seed_here:  # TODO: what happens when design is not square? TODO: what happens if the seeds needs to be moved somewhere else in the Y-direction?  The system needs to be more robust.
        seed_name = 'x-%s-n%s' % (y_position, slat_pos_id)
        seed_data = seed_plug_plate[seed_plug_plate['description'].str.contains(seed_name)]
        if len(seed_data) > 0:
            return [sanitize_plate_map(seed_plug_plate_corner), seed_data['well'].values[0], seed_data['sequence'].values[0]]

    if cargo_val > 0:  # TODO: 'cargo plate' needs to be updated with the real cargo plate's name!
        sel_location = cargo_plate[cargo_plate['Name'] == f'{cargo_name_dict[cargo_val]}_h2_cargo_handle_{slat_pos_id+1}']
        return ['cargo_plate', sel_location['WellPosition'].values[0], sel_location['Sequence'].values[0]]
    else:
        sel_plate = core_slat_plate
        core_name = 'slatcore-%s-h2ctrl' % (slat_pos_id + 1)
        sel_location = sel_plate[sel_plate['name'].str.contains(core_name)]
        return [sanitize_plate_map(slat_core), sel_location['well'].values[0], sel_location['sequence'].values[0]]


def collate_design_print_echo_commands(base_array, x_slats, y_slats, handle_array,
                                       x_cargo_map, y_cargo_map, cargo_name_dict,
                                       cargo_plate, destination_plate_name,
                                       output_folder, output_filename, include_seed=True, cargo_bearing_h5=False):
    # TODO: this is slow, needs speed-up
    core_slat_plate = read_dna_plate_mapping(os.path.join(plate_folder, slat_core + '.xlsx'))
    seed_plug_plate = read_dna_plate_mapping(os.path.join(plate_folder, seed_plug_plate_corner + '.xlsx'))

    x_crisscross_plates = []
    y_crisscross_plates = []

    staple_selection_x = defaultdict(list)
    staple_selection_y = defaultdict(list)

    for index, plate in enumerate(crisscross_handle_plates):  # first 3 plates are x-slat plates, next 3 are y-slat plates
        plate_df = read_dna_plate_mapping(os.path.join(plate_folder, plate + '.xlsx'))
        if index < 3:
            x_crisscross_plates.append([plate_df, plate])
        else:
            y_crisscross_plates.append([plate_df, plate])

    # TODO: this is super convoluted, need to simplify attaching a control, handle or cargo to a specific position, regardless of it being H2 or H5
    # H5 attachments
    for x in x_slats:
        handle_ids = handle_array[np.where(base_array[..., 0] == x)]
        if cargo_bearing_h5:
            staple_selection_x[x].extend(extract_h5_staples(handle_ids, core_slat_plate, x_crisscross_plates,
                                                            cargo_plate=cargo_plate, cargo_name_dict=cargo_name_dict,
                                                            cargo_bearing=True))
        else:
            staple_selection_x[x].extend(extract_h5_staples(handle_ids, core_slat_plate, x_crisscross_plates))

    for y in y_slats:
        handle_ids = handle_array[np.where(base_array[..., 1] == y)]
        staple_selection_y[y].extend(extract_h5_staples(handle_ids, core_slat_plate, y_crisscross_plates))

    # H2 attachments
    for i in range(x_cargo_map.shape[0]):
        for j in range(x_cargo_map.shape[1]):
            x_slat_id = base_array[i, j][0]
            y_slat_id = base_array[i, j][1]
            if x_slat_id != 0:
                staple_selection_x[x_slat_id].append(extract_cargo_staples(x_cargo_map[i, j], j, cargo_name_dict, core_slat_plate, cargo_plate, include_seed, seed_plug_plate, y_position=i+1))
            if y_slat_id != 0:
                staple_selection_y[y_slat_id].append(extract_cargo_staples(y_cargo_map[i, j], i, cargo_name_dict, core_slat_plate, cargo_plate))

    # echo command prep
    complete_list = []
    transfer_volume = 75
    source_plate_type = '384PP_AQ_BP'
    total_wells = 0
    for x_slat, package in staple_selection_x.items():
        for com_index, command in enumerate(package):
            complete_list.append(['x-slat_%s-command_%s' % (x_slat, com_index), command[0], command[1], plate96[total_wells], transfer_volume, destination_plate_name, source_plate_type])
        total_wells += 1
    for y_slat, package in staple_selection_y.items():
        for com_index, command in enumerate(package):
            complete_list.append(['y-slat_%s-command_%s' % (y_slat, com_index), command[0], command[1], plate96[total_wells], transfer_volume, destination_plate_name, source_plate_type])
        total_wells += 1

    combined_df = pd.DataFrame(complete_list, columns=['Component', 'Source Plate Name', 'Source Well', 'Destination Well', 'Transfer Volume', 'Destination Plate Name', 'Source Plate Type'])
    combined_df.to_csv(os.path.join(output_folder, output_filename), index=False)

    return combined_df
    # setup core staples - done separately
    # setup H5 staples (crisscross handles) - OK
    # setup H2 staples (cargo handles) - OK
    # setup H2 control staples (remainder) - OK
    # setup special staples (e.g. crossbar) - IN PROGRESS
    # setup seed attachment sockets/plugs - OK


