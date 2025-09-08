import copy

import numpy as np
import os

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.assembly_handle_optimization.random_hamming_optimizer import generate_handle_set_and_optimize
from crisscross.core_functions.slats import get_slat_key, Slat
from crisscross.plate_mapping.plate_constants import octahedron_patterning_v1, cargo_plate_folder
from crisscross.plate_mapping import get_standard_plates, get_plateclass

########################################
# script setup
design_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/tmsd_demos/split_design'
np.random.seed(8)

basic_file = 'slat_sketch.xlsx'
design_file = 'slat_sketch_with_unique_toehold_handles.xlsx'
anchor_design_file = 'slat_sketch_with_unique_toehold_handles_and_purification_anchors.xlsx'
handle_optimization_export_file = 'slat_sketch_with_unique_toehold_handles.xlsx'

update_handles = False
core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate = get_standard_plates()
crossbar_plate = get_plateclass('GenericPlate', octahedron_patterning_v1, cargo_plate_folder)

########################################
# Actual megastructure
if update_handles:
    M1 = Megastructure(import_design_file=os.path.join(design_folder, basic_file))
    fake_array = copy.copy(M1.slat_array) # this fake array forces the generation of unique handles for the toehold region, despite there not being any y-slats there
    fake_array[1:33, 48, 1] = 29
    fake_array[1:33, 49, 1] = 30
    fake_array[1:33, 50, 1] = 31
    fake_array[1:33, 51, 1] = 32
    handle_array = generate_handle_set_and_optimize(fake_array, unique_sequences=32, max_rounds=500)
    handle_array[1:17, 48:52, 0] = 0  # removes handles from non toehold regions
    M1.assign_assembly_handles(handle_array)
    M1.export_design(handle_optimization_export_file, design_folder)
else:
    for selected_file, design_id in [(design_file, 'no_cargo'), (anchor_design_file, 'with_anchors')]:
        M1 = Megastructure(import_design_file=os.path.join(design_folder, selected_file))
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
            [crisscross_handle_x_plates, crisscross_antihandle_y_plates, seed_plate, crossbar_plate],
            ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo'])
        M1.patch_flat_staples(control_plate=core_plate)

        invader_set = {}
        incumbent_slat_id_list = list(range(17, 33))
        # the actual invaders for the central region are designed here
        for i in range(16):
            invader = Slat(f'Invader {i + 1}', 'FLOATING', 'N/A')
            target_slat = M1.slats[get_slat_key(1, incumbent_slat_id_list[i])]
            for j in range(32):
                # the H2 side needs to have the entire set of matching antihandles to those on the target incumbent slats
                handle_coordinate = target_slat.slat_position_to_coordinate[j + 1]
                matching_handle = M1.handle_arrays[handle_coordinate[0], handle_coordinate[1], 0]

                invader.set_handle(j + 1, 2,
                                   crisscross_antihandle_y_plates.get_sequence(j + 1, 2, matching_handle),
                                   crisscross_antihandle_y_plates.get_well(j + 1, 2, matching_handle),
                                   crisscross_antihandle_y_plates.get_plate_name(j + 1, 2, matching_handle))

                # full control layer on the H5 side
                invader.set_handle(j + 1, 5,
                                   core_plate.get_sequence(j + 1, 5, 0),
                                   core_plate.get_well(j + 1, 5, 0),
                                   core_plate.get_plate_name(j + 1, 5, 0))
            invader_set[f'Invader {i + 1} matching slat {incumbent_slat_id_list[i]}'] = invader

        convert_slats_into_echo_commands(slat_dict={**M1.slats, **invader_set},
                                         destination_plate_name='split_tmsd_plate',
                                         default_transfer_volume=150,
                                         output_folder=design_folder,
                                         center_only_well_pattern=True,
                                         output_filename=f'echo_complete_design_{design_id}.csv')

        M1.create_standard_graphical_report(os.path.join(design_folder, f'design_graphics_{design_id}'), colormap='Set1',
                                            cargo_colormap='Dark2',
                                            generate_3d_video=True,
                                            seed_color=(1.0, 1.0, 0.0))

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

        M1.create_blender_3D_view(os.path.join(design_folder, f'design_graphics_{design_id}'), colormap='Set1',
                                  seed_color=(1.0, 1.0, 0.0),
                                  cargo_colormap='Dark2',
                                  animate_assembly=True,
                                  animation_type='translate',
                                  custom_assembly_groups=custom_animation_dict,
                                  camera_spin=False)
