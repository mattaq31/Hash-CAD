import numpy as np
import os
import pandas as pd

from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_precise_hamming
from crisscross.slat_handle_match_evolver.random_hamming_optimizer import generate_handle_set_and_optimize
from crisscross.plate_mapping.plate_constants import cargo_plate_folder, nelson_quimby_antihandles
from crisscross.plate_mapping import get_plateclass, get_standard_plates
########################################
# script setup
template_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/tmsd_demos/basic_square_tests_v1'
glider_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/gliders/design_v2'

np.random.seed(8)
read_handles_from_file = True
########################################
# Plate sequences
core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate = get_standard_plates()
nelson_plate = get_plateclass('GenericPlate', nelson_quimby_antihandles, cargo_plate_folder)
cargo_key = {3: 'antiNelson'}
########################################

########################################
# Shape generation and crisscross handle optimisation
slat_array, unique_slats_per_layer = generate_standard_square_slats(32)  # standard square

# assembly handle optimization (currently reading in design from crossbar megastructure)
if read_handles_from_file:
    handle_array = np.loadtxt(os.path.join(template_folder, 'optimized_handle_array.csv'), delimiter=',').astype(np.float32)
    handle_array = handle_array[..., np.newaxis]
    result = multirule_precise_hamming(slat_array, handle_array)
    print('Hamming distance from file-loaded design: %s' % result['Universal'])
else:
    handle_array = generate_handle_set_and_optimize(slat_array, unique_sequences=32, min_hamming=29, max_rounds=150)
########################################
# preparing seed placement (assumed to be center of megastructure)
insertion_seed_array = np.arange(16) + 1
insertion_seed_array = np.pad(insertion_seed_array[:, np.newaxis], ((0, 0), (4, 0)), mode='edge')

center_seed_array = np.zeros((32, 32))
center_seed_array[8:24, 13:18] = insertion_seed_array

########################################
# Actual megastructure
M1 = Megastructure(slat_array, layer_interface_orientations=[2, (5, 2), 5])
M1.assign_assembly_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
M1.assign_seed_handles(center_seed_array, center_seed_plate)
M1.patch_flat_staples(core_plate)
# M1.create_blender_3D_view('/Users/matt/Desktop', animate_assembly=True)

design_df = pd.read_excel(os.path.join(glider_folder, 'layer_arrays.xlsx'), sheet_name=None, header=None)
slat_array = np.zeros((design_df['Layer_0'].shape[0], design_df['Layer_0'].shape[1], len(design_df)))
for i, key in enumerate(design_df.keys()):
    slat_array[..., i] = design_df[key].values

slat_array[slat_array == -1] = 0  # removes the seed values, will re-add them later

seed_array = np.copy(design_df['Layer_0'].values)
seed_array[seed_array > 0] = 0
far_right_seed_pos = np.where(seed_array == -1)[1].max()
for i in range(16):
    column = far_right_seed_pos - i
    filler = (seed_array[:, column] == -1) * (i + 1)
    seed_array[:, column] = filler

M2 = Megastructure(slat_array, connection_angle='60')

for rev_slat in range(48, 64):  # this intervention is being done to accommodate the seed plate handles we have available
    M2.slats[f'layer2-slat{rev_slat}'].reverse_direction()

M2.assign_seed_handles(seed_array, seed_plate, layer_id=2)

custom_glider_animation_dict = {}

groups = [['layer2-slat%s' % x for x in range(48, 64)],
          ['layer3-slat%s' % x for x in range(96, 128)],
          ['layer2-slat%s' % x for x in range(32, 48)],
          ['layer4-slat%s' % x for x in range(160, 177)],
          ['layer3-slat%s' % x for x in range(128, 144)],
          ['layer2-slat%s' % x for x in range(64, 96)],
          ['layer3-slat%s' % x for x in range(144, 160)],
          ['layer4-slat%s' % x for x in range(177, 192)],
          ['layer1-slat%s' % x for x in range(1, 17)],
          ['layer1-slat%s' % x for x in range(17, 32)],
          ]
for order, group in enumerate(groups):
    for slat in group:
        custom_glider_animation_dict[slat] = order

slat_translate_dict = {}
for slat in groups[8] + groups[9]:
    slat_translate_dict[slat] = 20

# M2.export_design('full_design.xlsx', '/Users/matt/Desktop')
M2.create_standard_graphical_report(os.path.join('/Users/matt/Desktop', 'Design Graphics'), colormap='Set1',
                                             cargo_colormap='Dark2', seed_color=(1.0, 0.0, 0.0))

M2.create_blender_3D_view('/Users/matt/Desktop', animate_assembly=True,
                          animation_type='translate',
                          camera_spin=True,
                          custom_assembly_groups=custom_glider_animation_dict,
                          slat_translate_dict=slat_translate_dict)
