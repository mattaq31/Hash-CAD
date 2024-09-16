# this design implements a two-point bead purification system, which allows the megastructure to be purified using beads twice
import copy

import numpy as np
import os

from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.core_functions.megastructures import Megastructure
from crisscross.assembly_handle_optimization.hamming_compute import multirule_precise_hamming
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.plate_constants import (octahedron_patterning_v1, cargo_plate_folder)
from crisscross.plate_mapping import get_plateclass, get_standard_plates

########################################
# script setup
output_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/two_point_bead_purification/design_iteration_1'
plate_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/two_point_bead_purification/plate_order'
echo_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/two_point_bead_purification/design_iteration_1/echo_commands'

create_dir_if_empty(output_folder, echo_folder)
np.random.seed(8)
read_handles_from_file = True
########################################
# Plate sequences
core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate = get_standard_plates()
crossbar_plate = get_plateclass('GenericPlate', octahedron_patterning_v1, cargo_plate_folder)
########################################
# Shape generation and crisscross handle optimisation
slat_array, _ = generate_standard_square_slats(32)
# read in handles
handle_array = np.load(os.path.join(output_folder, 'true_mighty_29_square.npy'))
result = multirule_precise_hamming(slat_array, handle_array)
print('Hamming distance from file-loaded design: %s' % result['Universal'])

anchor_placement_array_lhs = np.zeros((32, 32))  # sequences will be placed on either end of the final set of slats
anchor_placement_array_lhs[16::2, 0] = 1

anchor_placement_array_rhs = np.zeros((32, 32))  # sequences will be placed on either end of the final set of slats
anchor_placement_array_rhs[16::2, 31] = 1
########################################
# preparing seed placement
insertion_seed_array = np.arange(16) + 1
insertion_seed_array = np.pad(insertion_seed_array[:, np.newaxis], ((0, 0), (4, 0)), mode='edge')
corner_seed_array = np.zeros((32, 32))
corner_seed_array[0:16, 0:5] = insertion_seed_array
########################################
M_base = Megastructure(slat_array)
M_base.assign_crisscross_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
M_base.assign_seed_handles(corner_seed_array, seed_plate)

all_megas = {}
for design in ['p1_anchors_inner', 'p32_anchors_inner', 'p1_anchors_outer', 'p32_anchors_outer']:
    all_megas[design] = copy.deepcopy(M_base)

    if design == 'p1_anchors_inner':
        anchor_name = 'Anchor-Wiggum-Flanders-inner-toehold'
        array_design = anchor_placement_array_lhs
    elif design == 'p32_anchors_inner':
        anchor_name = 'Anchor-Wiggum-Flanders-inner-toehold'
        array_design = anchor_placement_array_rhs
    elif design == 'p1_anchors_outer':
        anchor_name = 'Anchor-Wiggum-Flanders-outer-toehold'
        array_design = anchor_placement_array_lhs
    elif design == 'p32_anchors_outer':
        anchor_name = 'Anchor-Wiggum-Flanders-outer-toehold'
        array_design = anchor_placement_array_rhs

    all_megas[design].assign_cargo_handles_with_array(array_design,
                                                      cargo_plate=crossbar_plate,
                                                      cargo_key={1: anchor_name},
                                                      layer='bottom')
    all_megas[design].patch_control_handles(core_plate)
    if design == 'p32_anchors_inner':
        # all_megas[design].create_standard_graphical_report(os.path.join(output_folder, 'quick_viz'), colormap='Set1', cargo_colormap='Dark2', seed_color=(1.0, 1.0, 0.0))
        all_megas[design].create_blender_3D_view(os.path.join(output_folder, 'quick_viz'), colormap='Set1', cargo_colormap='Dark2', seed_color=(1.0, 1.0, 0.0), include_bottom_light=True)

M_base.patch_control_handles(core_plate)

full_slat_dict = {}

for i in range(17, 33):  # basic slats, no modifications
    full_slat_dict[f'no-modification-layer1-slat{i}'] = M_base.slats[f'layer1-slat{i}']

for design, mega in all_megas.items():
    for i in range(17, 33):  # basic slats, no modifications
        if all_megas[design].slats[f'layer1-slat{i}'].H2_handles[1]['plate'] == 'P3518_MA' or all_megas[design].slats[f'layer1-slat{i}'].H2_handles[32]['plate'] == 'P3518_MA':
            full_slat_dict[f'{design}-layer1-slat{i}'] = all_megas[design].slats[f'layer1-slat{i}']


# convert_slats_into_echo_commands(slat_dict=M_base.slats,
#                                  destination_plate_name='double_purification_plate',
#                                  default_transfer_volume=150,
#                                  unique_transfer_volume_for_plates={'P3518_MA': int(150*(500/200))},
#                                  output_folder=echo_folder,
#                                  center_only_well_pattern=True,
#                                  output_empty_wells=True,
#                                  output_filename=f'echo_complete_29_design_no_modifications.csv')
#
# convert_slats_into_echo_commands(slat_dict=full_slat_dict,
#                                  destination_plate_name='double_purification_plate',
#                                  default_transfer_volume=150,
#                                  unique_transfer_volume_for_plates={'P3518_MA': int(150*(500/200))},
#                                  output_folder=echo_folder,
#                                  center_only_well_pattern=True,
#                                  output_empty_wells=True,
#                                  output_filename=f'echo_complete_dbl_purification_anchors.csv')

