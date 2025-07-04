import os

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates, get_cutting_edge_plates

########################################
# NOTES

# This contains 4 x 16 = 64 nucX slats with different symmetries
# Also has the classic 4 x 16 = 64 directional growth slats

########################################
# SETUP
design_folder = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW132_repeatingunitassembly_epmotion_smallscale'
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
# 2 files, will be two separate plates

nucXslats = Megastructure(import_design_file=os.path.join(design_folder, 'nucX_design.xlsx'))
nucXslats.patch_placeholder_handles(
        [crisscross_handle_x_plates, crisscross_antihandle_y_plates, all_8064_seed_plugs, src_007, src_004, P3510],
        ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo', 'Cargo'])
nucXslats.patch_control_handles(core_plate)

echo_sheet_standard = convert_slats_into_echo_commands(slat_dict=nucXslats.slats,
                                                        destination_plate_name='repeating_epmotion_nucX_plate',
                                                        default_transfer_volume=100,
                                                        output_folder=echo_folder,
                                                        center_only_well_pattern=True,
                                                        plate_viz_type='barcode',
                                                        output_filename=f'SW132_echo_base_commands_nucXslats.csv')

repeatingunits = Megastructure(import_design_file=os.path.join(design_folder, 'directions_design.xlsx'))
repeatingunits.patch_placeholder_handles(
        [crisscross_handle_x_plates, crisscross_antihandle_y_plates, all_8064_seed_plugs, src_007, src_004, P3510],
        ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo', 'Cargo'])
repeatingunits.patch_control_handles(core_plate)

echo_sheet_standard = convert_slats_into_echo_commands(slat_dict=repeatingunits.slats,
                                                        destination_plate_name='repeating_epmotion_directions_plate',
                                                        default_transfer_volume=250,
                                                        output_folder=echo_folder,
                                                        center_only_well_pattern=True,
                                                        plate_viz_type='barcode',
                                                        output_filename=f'SW132_echo_base_commands_repeatingunits.csv')
