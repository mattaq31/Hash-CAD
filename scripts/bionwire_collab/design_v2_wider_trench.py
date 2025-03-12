import os
import numpy as np
import copy
import sys
import pandas as pd

from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates
from scripts.antigen_presenting_cells.capc_pattern_generator import capc_pattern_generator

########################################
# SETUP
design_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/bionwire/wide_trench_design'
experiment_name = 'SWXXX'
echo_folder = os.path.join(design_folder, 'echo_commands')
lab_helper_folder = os.path.join(design_folder, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True
compute_hamming = True
new_sequence_plate_generation = False
export_trench_design = True

np.random.seed(8)
# TODO: run the evolution algorithm for 64-seq
core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, _, _, _, combined_seed_plate_8064 = get_standard_plates(handle_library_v2=True)
src_004, src_005, src_007, P3518, P3510, P3628 = get_cargo_plates()
########################################
# STANDARD MEGASTRUCTURE
M1 = Megastructure(import_design_file=os.path.join(design_folder, 'full_design.xlsx'))
M1.patch_placeholder_handles(
    [crisscross_handle_x_plates, crisscross_antihandle_y_plates, combined_seed_plate_8064, src_007, src_004],
    ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo'])
M1.patch_control_handles(core_plate)
########################################
# TRENCH MEGASTRUCTURE
##################
# megastructure slat and trench prep
trench_slat_array = copy.copy(M1.slat_array)
slats_to_delete = np.array([119, 120, 183, 184, 59, 60, 26, 27, 58, 61, 62, 25, 28, 29, 118, 121, 122, 182, 185, 186])
slats_with_trench_handles = np.array([120, 184, 60, 27])
trench_slat_array[np.isin(trench_slat_array, slats_to_delete)] = 0
M_trench = Megastructure(trench_slat_array)

# TODO: REPLACE THESE WITH DNA PAINT STRANDS OR OTHER INTERESTING CARGO TYPES
# cargo_array_pd = capc_pattern_generator('peripheral_dispersed', total_cd3_antigens=192, capc_length=66)
# cargo_array_pd[trench_slat_array[..., 1] == 0] = 0
# M_trench.assign_cargo_handles_with_array(cargo_array_pd, cargo_key={1: 'antiBart', 2: 'antiEdna'}, layer='top')

# adds special trench handles to top layer
trench_cargo_array = np.zeros((trench_slat_array.shape[0], trench_slat_array.shape[1]))
trench_cargo_array[np.isin(M1.slat_array[..., 0], slats_with_trench_handles)] = 3  # places cargo in trench
trench_cargo_array[np.any(trench_cargo_array == 1, axis=1), :] = 3  # fill up staggered pattern
trench_cargo_array[
    np.isin(M1.slat_array[..., 1], slats_with_trench_handles)] = 0  # removes cargo from pass-through cavity
trench_cargo_array[trench_slat_array[..., 1] == 0] = 0  # removes cargo from edges of design
M_trench.assign_cargo_handles_with_array(trench_cargo_array, cargo_key={3: 'GoldWireBinder'}, layer=2, handle_orientation=2)

# adds special trench handles to bottom layer
trench_cargo_array = np.zeros((trench_slat_array.shape[0], trench_slat_array.shape[1]))
trench_cargo_array[np.isin(M1.slat_array[..., 1], slats_with_trench_handles)] = 3  # places cargo in trench
trench_cargo_array[:, np.any(trench_cargo_array == 1, axis=0)] = 3  # fill up staggered pattern
trench_cargo_array[
    np.isin(M1.slat_array[..., 0], slats_with_trench_handles)] = 0  # removes cargo from pass-through cavity
trench_cargo_array[trench_slat_array[..., 0] == 0] = 0  # removes cargo from edges of design
M_trench.assign_cargo_handles_with_array(trench_cargo_array, cargo_key={3: 'GoldWireBinder'}, layer=1, handle_orientation=5)

##################
# new sequence preparation
if new_sequence_plate_generation:
    nanowire_handle_sequence = 'GGTTGATAAAAGCATGACAGGTTGATAATATAGAT'
    all_handles_required = set()
    for slat_id, slat in M_trench.slats.items():
        for placeholder in slat.placeholder_list:
            all_handles_required.add(placeholder)

    names = []
    descriptions = []
    sequences = []
    for handle in sorted(all_handles_required):
        slat_pos = int(handle.split('-')[1])
        slat_side = int(handle.split('-')[2].split('h')[-1])
        new_seq = core_plate.get_sequence(slat_pos, slat_side) + 'tt' + nanowire_handle_sequence
        names.append(f'GoldWireBinder_h{slat_side}_pos{slat_pos}')
        descriptions.append(f'Binding handle for the BioNWire gold nanowires at position {slat_pos} on side {slat_side}.')
        sequences.append(new_seq)
    df = pd.DataFrame([names, descriptions, sequences], index=['Names', 'Descriptions', 'Sequences'])
    df.to_excel(os.path.join(design_folder, "GoldWireBinder-NewSequences.xlsx"), header=False)

    print('%%%%%%%%%%%')
    print('Add required sequences (now exported to GoldWireBinder-NewSequences.xlsx) to cargo plate then re-run code with new_sequence_plate_generation=False.')
    print('%%%%%%%%%%%')
    sys.exit()
##################
# handle completion

# seed and assembly handles
M_trench.assign_seed_handles(M1.seed_array[1])
new_assembly_handle_array = copy.copy(M1.handle_arrays)
new_assembly_handle_array[(M_trench.slat_array[...,0] == 0) | (M_trench.slat_array[...,1] == 0)] = 0
M_trench.assign_crisscross_handles(new_assembly_handle_array)

# double purification handles
trench_dbl_purif_array = np.zeros((trench_slat_array.shape[0], trench_slat_array.shape[1]))
trench_dbl_purif_array[57:65, 48] = 4
M_trench.assign_cargo_handles_with_array(trench_dbl_purif_array, cargo_key={4: 'SSW041DoublePurification5primetoehold'}, layer='bottom')

M_trench.patch_placeholder_handles(
    [crisscross_handle_x_plates, crisscross_antihandle_y_plates, combined_seed_plate_8064, src_007, src_004, P3518],
    ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo', 'Cargo'])
M_trench.patch_control_handles(core_plate)

if export_trench_design:
    M_trench.export_design(os.path.join(design_folder, 'trench_design.xlsx'), design_folder)

########################################
# ECHO
nominal_handle_volume = 150
if generate_echo:
    echo_sheet_standard = convert_slats_into_echo_commands(slat_dict=M1.slats,
                                                           destination_plate_name='bionwire_no_trench_plate',
                                                           default_transfer_volume=nominal_handle_volume,
                                                           output_folder=echo_folder,
                                                           center_only_well_pattern=True,
                                                           plate_viz_type='barcode',
                                                           output_filename=f'echo_base_commands_no_trench.csv')

    echo_sheet_trench = convert_slats_into_echo_commands(slat_dict=M_trench.slats,
                                                         destination_plate_name='bionwire_trench_plate',
                                                         default_transfer_volume=nominal_handle_volume,
                                                         output_folder=echo_folder,
                                                         center_only_well_pattern=True,
                                                         plate_viz_type='barcode',
                                                         output_filename=f'wide_trench_echo_base_commands.csv')
########################################
# LAB PROCESSING
if generate_lab_helpers:
    prepare_all_standard_sheets(M1.slats, os.path.join(lab_helper_folder, f'{experiment_name}_no_trench_helpers.xlsx'),
                                reference_single_handle_volume=nominal_handle_volume,
                                reference_single_handle_concentration=500,
                                echo_sheet=None if not generate_echo else echo_sheet_standard,
                                peg_groups_per_layer=4)

    prepare_all_standard_sheets(M_trench.slats, os.path.join(lab_helper_folder, f'{experiment_name}_plus_with_trench_helpers.xlsx'),
                                reference_single_handle_volume=nominal_handle_volume,
                                reference_single_handle_concentration=500,
                                echo_sheet=None if not generate_echo else echo_sheet_trench,
                                peg_groups_per_layer=4)
########################################
# REPORTS
if compute_hamming:
    print('Hamming Distance Report:')
    print(multirule_oneshot_hamming(M1.slat_array, M1.handle_arrays,
                                    per_layer_check=True,
                                    report_worst_slat_combinations=False,
                                    request_substitute_risk_score=True))
########################################
# GRAPHICS
if generate_graphical_report:
    M1.create_standard_graphical_report(os.path.join(design_folder, 'standard_plus_visualization/'),
                                        colormap='Set1',
                                        cargo_colormap='Dark2',
                                        generate_3d_video=True,
                                        seed_color=(1.0, 1.0, 0.0))

    M1.create_blender_3D_view(os.path.join(design_folder, 'standard_plus_visualization/'),
                              colormap='Set1',
                              cargo_colormap='Dark2',
                              animate_assembly=False,
                              seed_color=(1.0, 1.0, 0.0),
                              camera_spin=False)

    M_trench.create_standard_graphical_report(os.path.join(design_folder, 'trench_plus_visualization/'),
                                              colormap='Set1',
                                              cargo_colormap='Dark2',
                                              generate_3d_video=True,
                                              seed_color=(1.0, 1.0, 0.0))

    M_trench.create_blender_3D_view(os.path.join(design_folder, 'trench_plus_visualization/'),
                                    colormap='Set1',
                                    cargo_colormap='Dark2',
                                    animate_assembly=False,
                                    seed_color=(1.0, 1.0, 0.0),
                                    camera_spin=False)
