import os
import numpy as np

from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.slat_design import read_design_from_excel
from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_precise_hamming
from crisscross.slat_handle_match_evolver.random_hamming_optimizer import generate_handle_set_and_optimize
from crisscross.plate_mapping import get_plateclass, get_standard_plates
from capc_pattern_generator import capc_pattern_generator

from crisscross.plate_mapping.plate_constants import cargo_plate_folder, octahedron_patterning_v1, nelson_quimby_antihandles, simpsons_mixplate_antihandles

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

    result = multirule_precise_hamming(slat_array, handle_array)
    print('Hamming distance from file-loaded design: %s' % result['Universal'])
else:
    handle_array = generate_handle_set_and_optimize(slat_array, unique_sequences=32, max_rounds=150)
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
core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate = get_standard_plates()
nelson_plate = get_plateclass('GenericPlate', nelson_quimby_antihandles, cargo_plate_folder)
octahedron_plate = get_plateclass('GenericPlate', octahedron_patterning_v1, cargo_plate_folder)
bart_edna_plate = get_plateclass('GenericPlate', simpsons_mixplate_antihandles, cargo_plate_folder)
cargo_key = {3: 'antiNelson', 1: 'antiBart', 2: 'antiEdna'}
########################################
# Preparing animation order for slats
# have to prepare these manually as the stagger is screwing up with the automatic detection system.
# The animation direction detector is also being turned off due to this issue.
# TODO: changing the direction of the slats so that they don't phase through other slats is still required for this kind of design.
custom_glider_animation_dict = {}

groups = [['layer1-slat%s' % x for x in range(98, 114)],
          ['layer2-slat%s' % x for x in range(17, 33)],
          ['layer1-slat%s' % x for x in range(130, 156)],
          ['layer2-slat%s' % x for x in range(33, 49)],
          ['layer1-slat%s' % x for x in range(162, 177)],
          ['layer2-slat%s' % x for x in range(82, 98)],
          ['layer1-slat%s' % x for x in range(177, 194)],
          ['layer2-slat%s' % x for x in range(66, 82)],
          ['layer1-slat%s' % x for x in range(146, 162)],
          ['layer2-slat%s' % x for x in range(50, 67)],
          ['layer1-slat%s' % x for x in range(114, 130)],
          ['layer2-slat%s' % x for x in range(1, 17)],
          ]
for order, group in enumerate(groups):
    for slat in group:
        custom_glider_animation_dict[slat] = order

########################################

M1_peripheral_dispersed = Megastructure(slat_array, layer_interface_orientations=[2, (5, 2), 5])
M1_peripheral_dispersed.assign_assembly_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
M1_peripheral_dispersed.assign_seed_handles(center_seed_array, center_seed_plate)
M1_peripheral_dispersed.assign_cargo_handles_with_array(cargo_array_pd, cargo_key, bart_edna_plate, layer='top')
M1_peripheral_dispersed.patch_flat_staples(core_plate)

M1_peripheral_dispersed.export_design('full_design.xlsx', design_folder)

# M1_peripheral_dispersed.create_standard_graphical_report(os.path.join(design_folder, 'design_graphics_peripheral_dispersed'),
#                                                          colormap='Dark2')
# M1_peripheral_dispersed.create_blender_3D_view(os.path.join(design_folder, 'design_graphics_peripheral_dispersed'), # I probably need to define the slats for each group manually...
#                                                custom_assembly_groups=custom_glider_animation_dict,
#                                                correct_slat_entrance_direction=False,
#                                                animate_assembly=True, animation_type='translate')


# M2_peripheral_bordered = Megastructure(slat_array, layer_interface_orientations=[2, (5, 2), 5])
# M2_peripheral_bordered.assign_crisscross_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
# M2_peripheral_bordered.assign_seed_handles(center_seed_array, center_seed_plate)
# M2_peripheral_bordered.assign_cargo_handles_with_array(cargo_array_pb, bart_edna_plate, cargo_key, layer='top')
# M2_peripheral_bordered.patch_control_handles(core_plate)
# M2_peripheral_bordered.create_standard_graphical_report(os.path.join(design_folder, 'design_graphics_peripheral_bordered'), colormap='Dark2')
#
# M3_centre_bordered = Megastructure(slat_array, layer_interface_orientations=[2, (5, 2), 5])
# M3_centre_bordered.assign_crisscross_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
# M3_centre_bordered.assign_seed_handles(center_seed_array, center_seed_plate)
# M3_centre_bordered.assign_cargo_handles_with_array(cargo_array_cb, bart_edna_plate, cargo_key, layer='top')
# M3_centre_bordered.patch_control_handles(core_plate)
# M3_centre_bordered.create_standard_graphical_report(os.path.join(design_folder, 'design_graphics_central_bordered'), colormap='Dark2')
#
# M4_centre_dispersed = Megastructure(slat_array, layer_interface_orientations=[2, (5, 2), 5])
# M4_centre_dispersed.assign_crisscross_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
# M4_centre_dispersed.assign_seed_handles(center_seed_array, center_seed_plate)
# M4_centre_dispersed.assign_cargo_handles_with_array(cargo_array_cd, bart_edna_plate, cargo_key, layer='top')
# M4_centre_dispersed.patch_control_handles(core_plate)
# M4_centre_dispersed.create_standard_graphical_report(os.path.join(design_folder, 'design_graphics_central_dispersed'), colormap='Dark2')
#
# M5_random = Megastructure(slat_array, layer_interface_orientations=[2, (5, 2), 5])
# M5_random.assign_crisscross_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
# M5_random.assign_seed_handles(center_seed_array, center_seed_plate)
# M5_random.assign_cargo_handles_with_array(cargo_array_rand, bart_edna_plate, cargo_key, layer='top')
# M5_random.patch_control_handles(core_plate)
# M5_random.create_standard_graphical_report(os.path.join(design_folder, 'design_graphics_random_patterning'), colormap='Dark2')
