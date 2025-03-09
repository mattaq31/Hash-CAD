from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.plate_mapping.plate_constants import simpsons_mixplate_antihandles, cargo_plate_folder
from crisscross.plate_mapping import get_standard_plates, get_plateclass
import os


main_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/3D_stacking'
design_folder = os.path.join(main_folder, 'designs')
echo_folder = os.path.join(main_folder, 'echo_commands')
graphics_required = False

core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate = get_standard_plates()
simpsons_mixplate = get_plateclass('GenericPlate', simpsons_mixplate_antihandles, cargo_plate_folder)

M1 = Megastructure(import_design_file=os.path.join(design_folder, 'H26_optimal_design_with_5_layers.xlsx'))
# note that the similarity risk score will be 0 since the 2nd and 4th handle arrays are repeated
print(multirule_oneshot_hamming(M1.slat_array, M1.handle_arrays,
                                per_layer_check=True,
                                report_worst_slat_combinations=False,
                                request_substitute_risk_score=True))

if graphics_required:
    M1.create_standard_graphical_report(os.path.join(main_folder, 'H26_5_layers_viz'),
                                        colormap='Set1',
                                        cargo_colormap='Dark2',
                                        seed_color=(1.0, 1.0, 0.0))

M1.patch_placeholder_handles(
    [crisscross_handle_x_plates, crisscross_antihandle_y_plates, combined_seed_plate, simpsons_mixplate],
    ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo'])

M1.patch_control_handles(core_plate)

target_slats = {}

for key, slat in M1.slats.items():  # the 5th layer is only there as a placeholder - we do not need to echo it again since it should be identical to layer 3
    if slat.layer < 5:
        target_slats[key] = slat

print('Total slats:', len(target_slats))

convert_slats_into_echo_commands(slat_dict=target_slats,
                                 destination_plate_name='stacker_plate',
                                 unique_transfer_volume_for_plates={'sw_src007': int(150*(500/200))},
                                 default_transfer_volume=150,
                                 output_folder=echo_folder,
                                 center_only_well_pattern=True,
                                 output_filename=f'4_layer_repeater_base_commands.csv')
