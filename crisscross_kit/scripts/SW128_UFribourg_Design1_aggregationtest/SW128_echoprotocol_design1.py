import os

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates, get_cutting_edge_plates

########################################
# NOTES

# This structure will be a standard H30 square but with over 500 handles (every other position has a handle)
# Three structures in total - 500+ handles with or without G's, and no handles (simple square)
# X slats will be made once (remove X slats for the second and third structures)
# No-handle version will actually be made using slats prepared 31 Y slats prepared in SW131, only prepare the position 16 Y slat here

########################################
# SETUP
design_folder = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW128_fribourg_design1_aggregationtest'
echo_folder = os.path.join(design_folder, 'echo_commands')
lab_helper_folder = os.path.join(design_folder, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True
compute_hamming = True
new_sequence_plate_generation = False
export_trench_design = True

core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, all_8064_seed_plugs = get_cutting_edge_plates()

src_004, src_005, src_007, P3518, P3510, P3628 = get_cargo_plates()

########################################
# 2 squares, but make X slats only once, and also only save the position 16 Y slat with controls alone

ACTsquare = Megastructure(import_design_file=os.path.join(design_folder, 'ACT_handles.xlsx'))
ACTsquare.patch_placeholder_handles(
        [crisscross_handle_x_plates, crisscross_antihandle_y_plates, all_8064_seed_plugs, src_007, src_004, P3510],
        ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo', 'Cargo'])
ACTsquare.patch_control_handles(core_plate)

echo_sheet_standard = convert_slats_into_echo_commands(slat_dict=ACTsquare.slats,
                                                        destination_plate_name='ufribourg_design1_h5ACThandles_plate',
                                                        default_transfer_volume=100,
                                                        output_folder=echo_folder,
                                                        center_only_well_pattern=True,
                                                        plate_viz_type='barcode',
                                                        output_filename=f'SW128_echo_base_commands_h5-ACThandle.csv')

# Combine the echo sheet and destination plate for G handle and no handle
Gsquare = Megastructure(import_design_file=os.path.join(design_folder, 'G_handles.xlsx'))
Gsquare.patch_placeholder_handles(
        [crisscross_handle_x_plates, crisscross_antihandle_y_plates, all_8064_seed_plugs, src_007, src_004, P3510],
        ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo', 'Cargo'])
Gsquare.patch_control_handles(core_plate)
GsquareYslats = {x:y for x,y in Gsquare.slats.items() if "layer2" in x}

# Just want position 16 Y slat
UnitSquare = Megastructure(import_design_file=os.path.join(design_folder, 'no_handles.xlsx'))
UnitSquare.patch_placeholder_handles(
        [crisscross_handle_x_plates, crisscross_antihandle_y_plates, all_8064_seed_plugs, src_007, src_004, P3510],
        ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo', 'Cargo'])
UnitSquare.patch_control_handles(core_plate)
GsquareYslats["layer2-slat16-nohandles"] = UnitSquare.slats["layer2-slat16"]

echo_sheet_standard = convert_slats_into_echo_commands(slat_dict=GsquareYslats,
                                                        destination_plate_name='ufribourg_design1_h5Ghandles_plate',
                                                        default_transfer_volume=100,
                                                        output_folder=echo_folder,
                                                        center_only_well_pattern=True,
                                                        plate_viz_type='barcode',
                                                        output_filename=f'SW128_echo_base_commands_h5-Ghandle.csv')

# Manually change E3 (Y slat16) transfers to 150 µL!
