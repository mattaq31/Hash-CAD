import numpy as np
import os

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.slat_design import generate_standard_square_slats, generate_patterned_square_cco
from crisscross.core_functions.hamming_functions import generate_random_slat_handles, generate_handle_set_and_optimize
from crisscross.core_functions.slats import get_slat_key
from crisscross.plate_mapping import get_standard_plates

########################################
# script setup
design_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/tmsd_demos/split_design'
np.random.seed(8)
design_file = 'slat_sketch_with_handles.xlsx'
updated_design_file = 'slat_sketch_with_handles_v2.xlsx'
update_handles = False
core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate = get_standard_plates()

########################################
# Actual megastructure
M1 = Megastructure(import_design_file=os.path.join(design_folder, design_file))
if update_handles:
    handle_array = generate_handle_set_and_optimize(M1.slat_array, unique_sequences=32, max_rounds=500)
    M1.assign_crisscross_handles(handle_array)
    M1.export_design(updated_design_file, design_folder)


# in this design we are trying a new system where the y-slat assembly handles are removed to try and enforce rigidity while allowing TMSD to occur.
# To do this, both the handles and placeholder list need to be updated.
handle_blocker = np.zeros_like(M1.handle_arrays)
handle_blocker[17:33, 44:48, 0] = 1
block_coords = np.where(handle_blocker == 1)

for y, x in zip(block_coords[0], block_coords[1]):
    slat_id = M1.slat_array[y, x, 1]
    sel_slat = M1.slats[get_slat_key(2, slat_id)]
    slat_posn = sel_slat.slat_coordinate_to_position[(y, x)]
    del sel_slat.H2_handles[slat_posn]
    sel_slat.placeholder_list.remove(f'handle-{slat_posn}-h2')

M1.patch_placeholder_handles(
    [crisscross_handle_x_plates, crisscross_antihandle_y_plates, seed_plate],
    ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed'])
M1.patch_control_handles(control_plate=core_plate)

convert_slats_into_echo_commands(slat_dict=M1.slats,
                                 destination_plate_name='split_tmsd_plate',
                                 default_transfer_volume=150,
                                 output_folder=design_folder,
                                 center_only_well_pattern=True,
                                 output_empty_wells=True,
                                 output_filename=f'echo_complete_design.csv')

M1.create_standard_graphical_report(os.path.join(design_folder, 'Design Graphics'), colormap='Set1', generate_3d_video=False,
                                    cargo_colormap=['#FFFF00', '#66ff00'], seed_color=(1.0, 1.0, 0.0))

custom_animation_dict = {}

groups = [['layer1-slat%s' % x for x in range(1, 17)],
          ['layer2-slat%s' % x for x in range(13, 29)],
          ['layer1-slat%s' % x for x in range(17, 33)],
          ['layer2-slat%s' % x for x in range(1, 13)],
          ['layer1-slat%s' % x for x in range(33, 49)],
          ]
for order, group in enumerate(groups):
    for slat in group:
        custom_animation_dict[slat] = order

M1.create_blender_3D_view(os.path.join(design_folder, 'Design Graphics'), colormap='Set1',
                          seed_color=(1.0, 1.0, 0.0),
                          cargo_colormap=['#FFFF00', '#66ff00'],
                          animate_assembly=True,
                          animation_type='translate',
                          custom_assembly_groups=custom_animation_dict,
                          camera_spin=False)
