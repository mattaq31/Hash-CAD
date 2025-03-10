import numpy as np
import os

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.helper_functions import create_dir_if_empty
from crisscross.plate_mapping import get_plateclass, get_standard_plates, get_cargo_plates
from crisscross.plate_mapping.plate_constants import seed_plug_plate_all_8064, core_plate_folder

core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate, all_8064_seed_plugs  = get_standard_plates()
p8064_seed_plate = get_plateclass('CombinedSeedPlugPlate', seed_plug_plate_all_8064, core_plate_folder)
src_004, src_005, src_007, P3518, P3510, P3628 = get_cargo_plates()
generate_echo = True
generate_lab_helpers = True
generate_graphical_report = True

design_folder = '/Users/yichenzhao/Documents/Wyss/Projects/CrissCross_Output/PAINT/10nt'
echo_folder = os.path.join(design_folder, 'echo_commands')
lab_helper_folder = os.path.join(design_folder, 'lab_helper_sheets')
hamming_folder = os.path.join(design_folder, 'hamming_arrays')
create_dir_if_empty(echo_folder, lab_helper_folder, hamming_folder)
experiment_name = 'YXZ003'


#slat_array, _ = generate_standard_square_slats(32)
slat_array = np.ones((1,32,1))

M1 = Megastructure(slat_array)

final_cargo_placement = np.zeros((1,32))

final_cargo_placement[0,0] = 1
final_cargo_placement[0,1] = 1
final_cargo_placement[0,3] = 1
final_cargo_placement[0,7] = 1
final_cargo_placement[0,15] = 1
final_cargo_placement[0,31] = 1

M1.assign_cargo_handles_with_array(final_cargo_placement, cargo_key={1: '10ntpaintp1'}, handle_orientation=5, layer=1)

M1.export_design('design1s2_10.xlsx',design_folder)

M1.patch_placeholder_handles(
    [P3628],
    ['Cargo'])

M1.patch_control_handles(core_plate)


if generate_echo:
    target_volume = 200
    special_vol_plates = {'sw_src007': int(target_volume * (500 / 200)),
                          'sw_src004': int(target_volume * (500 / 200)),
                          'P3621_SSW': int(target_volume * (500 / 200)),
                          'P3518_MA': int(target_volume * (500 / 200)),
                          'P3601_MA': int(target_volume * (500 / 100)),
                          'P3602_MA': int(target_volume * (500 / 100)),
                          'P3603_MA': int(target_volume * (500 / 100)),
                          'P3604_MA': int(target_volume * (500 / 100)),
                          'P3605_MA': int(target_volume * (500 / 100)),
                          'P3606_MA': int(target_volume * (500 / 100)),
                          'P3628_SSW': int(target_volume * (500 / 200))}

    echo_sheet = convert_slats_into_echo_commands(slat_dict=M1.slats,
                                                  destination_plate_name='sslat10_plate',
                                                  unique_transfer_volume_for_plates=special_vol_plates,
                                                  default_transfer_volume=target_volume,
                                                  output_folder=echo_folder,
                                                  center_only_well_pattern=True,
                                                  plate_viz_type='barcode',
                                                  output_filename=f'sslat10_echo_base_commands.csv')

if generate_lab_helpers:
    prepare_all_standard_sheets(M1.slats, os.path.join(lab_helper_folder, f'{experiment_name}_standard_helpers.xlsx'),
                                reference_single_handle_volume=target_volume,
                                reference_single_handle_concentration=500,
                                echo_sheet=None if not generate_echo else echo_sheet,
                                peg_groups_per_layer=2,
                                unique_transfer_volume_plates=special_vol_plates)

if generate_graphical_report:
    M1.create_standard_graphical_report(os.path.join(design_folder, 'visualization/'),
                                        colormap='Set1',
                                        cargo_colormap='Dark2',
                                        generate_3d_video=True,
                                        seed_color=(1.0, 1.0, 0.0))
