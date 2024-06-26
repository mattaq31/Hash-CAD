import pandas as pd
import os
import numpy as np
from colorama import Fore

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.slat_design import generate_handle_set_and_optimize, calculate_slat_hamming, read_design_from_excel
from crisscross.plate_mapping import get_plateclass
from capc_pattern_generator import capc_pattern_generator

from crisscross.helper_functions.plate_constants import (slat_core, core_plate_folder, crisscross_h5_handle_plates,
                                                         crisscross_h2_handle_plates, assembly_handle_folder,
                                                         seed_plug_plate_center, cargo_plate_folder, octahedron_patterning_v1,
                                                         nelson_quimby_antihandles, simpsons_mixplate_antihandles, seed_plug_plate_corner)

design_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/CAPCs/version_1'
read_handles_from_file = True
np.random.seed(8)
slat_array = read_design_from_excel(design_folder, ['main_slats_bottom.csv', 'main_slats_top.csv'])

total_cd3_antigens = 192
cargo_array_pd = capc_pattern_generator('peripheral_dispersed', total_cd3_antigens=total_cd3_antigens, capc_length=66)
cargo_array_pb = capc_pattern_generator('peripheral_bordered', total_cd3_antigens=total_cd3_antigens, capc_length=66)
cargo_array_cd = capc_pattern_generator('central_dispersed', total_cd3_antigens=total_cd3_antigens, capc_length=66)
cargo_array_cb = capc_pattern_generator('central_bordered', total_cd3_antigens=total_cd3_antigens, capc_length=66)
cargo_array_rand = capc_pattern_generator('random', slat_mask=slat_array, total_cd3_antigens=total_cd3_antigens, capc_length=66)

########################################
# assembly handle optimization (currently reading in design from Stella's original plus-shaped megastructure)
if read_handles_from_file:
    handle_array = np.loadtxt(os.path.join(design_folder, 'legacy_assembly_handles.csv'), delimiter=',').astype(
        np.float32)
    handle_array = handle_array[..., np.newaxis]

    unique_slats_per_layer = []
    for i in range(slat_array.shape[2]):
        slat_ids = np.unique(slat_array[:, :, i])
        slat_ids = slat_ids[slat_ids != 0]
        unique_slats_per_layer.append(slat_ids)

    _, _, res = calculate_slat_hamming(slat_array, handle_array, unique_slats_per_layer, unique_sequences=32)
    print('Hamming distance from file-loaded design: %s' % np.min(res))
else:
    handle_array = generate_handle_set_and_optimize(slat_array, unique_sequences=32, min_hamming=29, max_rounds=150)
    np.savetxt(os.path.join(design_folder, 'optimized_handle_array.csv'), handle_array.squeeze().astype(np.int32),
               delimiter=',', fmt='%i')
########################################
# seed placement - center of first set of x-slats
insertion_seed_array = np.arange(16) + 1
insertion_seed_array = np.pad(insertion_seed_array[:, np.newaxis], ((0, 0), (4, 0)), mode='edge')

center_seed_array = np.zeros((66, 66))
center_seed_array[17:33, 14:14+5] = insertion_seed_array
########################################
# Plate sequences
core_plate = get_plateclass('ControlPlate', slat_core, core_plate_folder)
crisscross_antihandle_y_plates = get_plateclass('CrisscrossHandlePlates',
                                                crisscross_h5_handle_plates[3:] + crisscross_h2_handle_plates,
                                                assembly_handle_folder, plate_slat_sides=[5, 5, 5, 2, 2, 2])
crisscross_handle_x_plates = get_plateclass('CrisscrossHandlePlates', crisscross_h5_handle_plates[0:3],
                                            assembly_handle_folder, plate_slat_sides=[5, 5, 5])
seed_plate = get_plateclass('CornerSeedPlugPlate', seed_plug_plate_corner, core_plate_folder)
center_seed_plate = get_plateclass('CenterSeedPlugPlate', seed_plug_plate_center, core_plate_folder)
nelson_plate = get_plateclass('AntiNelsonQuimbyPlate', nelson_quimby_antihandles, cargo_plate_folder)
octahedron_plate = get_plateclass('OctahedronPlate', octahedron_patterning_v1, cargo_plate_folder)
bart_edna_plate = get_plateclass('SimpsonsMixPlate', simpsons_mixplate_antihandles, cargo_plate_folder)
########################################

M1_peripheral_dispersed = Megastructure(slat_array, layer_interface_orientations=[2, (5, 2), 5])
M1_peripheral_dispersed.assign_crisscross_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
M1_peripheral_dispersed.assign_seed_handles(center_seed_array, center_seed_plate)
M1_peripheral_dispersed.assign_cargo_handles(cargo_array_pd, bart_edna_plate, layer='top')
M1_peripheral_dispersed.patch_control_handles(core_plate)
M1_peripheral_dispersed.create_standard_graphical_report(os.path.join(design_folder, 'design_graphics_peripheral_dispersed'),
                                                         colormap='Dark2')

M2_peripheral_bordered = Megastructure(slat_array, layer_interface_orientations=[2, (5, 2), 5])
M2_peripheral_bordered.assign_crisscross_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
M2_peripheral_bordered.assign_seed_handles(center_seed_array, center_seed_plate)
M2_peripheral_bordered.assign_cargo_handles(cargo_array_pb, bart_edna_plate, layer='top')
M2_peripheral_bordered.patch_control_handles(core_plate)
M2_peripheral_bordered.create_standard_graphical_report(os.path.join(design_folder, 'design_graphics_peripheral_bordered'), colormap='Dark2')

M3_centre_bordered = Megastructure(slat_array, layer_interface_orientations=[2, (5, 2), 5])
M3_centre_bordered.assign_crisscross_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
M3_centre_bordered.assign_seed_handles(center_seed_array, center_seed_plate)
M3_centre_bordered.assign_cargo_handles(cargo_array_cb, bart_edna_plate, layer='top')
M3_centre_bordered.patch_control_handles(core_plate)
M3_centre_bordered.create_standard_graphical_report(os.path.join(design_folder, 'design_graphics_central_bordered'), colormap='Dark2')

M4_centre_dispersed = Megastructure(slat_array, layer_interface_orientations=[2, (5, 2), 5])
M4_centre_dispersed.assign_crisscross_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
M4_centre_dispersed.assign_seed_handles(center_seed_array, center_seed_plate)
M4_centre_dispersed.assign_cargo_handles(cargo_array_cd, bart_edna_plate, layer='top')
M4_centre_dispersed.patch_control_handles(core_plate)
M4_centre_dispersed.create_standard_graphical_report(os.path.join(design_folder, 'design_graphics_central_dispersed'), colormap='Dark2')

M5_random = Megastructure(slat_array, layer_interface_orientations=[2, (5, 2), 5])
M5_random.assign_crisscross_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
M5_random.assign_seed_handles(center_seed_array, center_seed_plate)
M5_random.assign_cargo_handles(cargo_array_rand, bart_edna_plate, layer='top')
M5_random.patch_control_handles(core_plate)
M5_random.create_standard_graphical_report(os.path.join(design_folder, 'design_graphics_random_patterning'), colormap='Dark2')
