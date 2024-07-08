import numpy as np
import os
import copy
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from colorama import Fore

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.core_functions.hamming_functions import generate_handle_set_and_optimize, multi_rule_hamming
from crisscross.core_functions.slats import Slat

from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.plate_constants import (slat_core, core_plate_folder, assembly_handle_folder,
                                                         crisscross_h5_handle_plates, crisscross_h2_handle_plates,
                                                         seed_plug_plate_corner, seed_plug_plate_center,
                                                         cargo_plate_folder, nelson_quimby_antihandles,
                                                         octahedron_patterning_v1, simpsons_mixplate_antihandles)
from crisscross.plate_mapping import get_plateclass
from crisscross.helper_functions.plate_constants import plate96

################################
# script setup
output_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/tmsd_demos/basic_square_tests_v6'
create_dir_if_empty(output_folder)
np.random.seed(8)
read_handles_from_file = True
regenerate_graphics = False
################################
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
bart_plate = get_plateclass('OctahedronPlate', octahedron_patterning_v1, cargo_plate_folder)
simpsons_plate = get_plateclass('SimpsonsMixPlate', simpsons_mixplate_antihandles, cargo_plate_folder)
################################

################################
# Shape generation and crisscross handle optimisation

slat_array, unique_slats_per_layer = generate_standard_square_slats(32)  # standard square

padded_slat_array = np.pad(slat_array, ((20, 20), (1, 1), (0, 0)), mode='constant', constant_values=0)
for slat_invader_placement in [17, 18, 19, 20, 21, 22, 23, 24]:  # all the hot slats are now replaced in this extension
    padded_slat_array[padded_slat_array[..., 1] == slat_invader_placement, 1] = 0
    padded_slat_array[4:36, slat_invader_placement, 1] = slat_invader_placement

# assembly handle optimization (currently reading in design from crossbar megastructure)
if read_handles_from_file:
    handle_array = np.loadtxt(os.path.join(output_folder, 'optimized_handle_array.csv'), delimiter=',').astype(
        np.float32)
    handle_array = handle_array[..., np.newaxis]
    result = multi_rule_hamming(slat_array, handle_array)
    print('Hamming distance from file-loaded design: %s' % result['Universal'])
else:
    handle_array = generate_handle_set_and_optimize(slat_array, unique_sequences=32, max_rounds=150)
    np.savetxt(os.path.join(output_folder, 'optimized_handle_array.csv'), handle_array.squeeze().astype(np.int32),
               delimiter=',', fmt='%i')

# This is a padded handle array to match the invader version of the design
padded_handle_array = np.pad(handle_array, ((20, 20), (1, 1), (0, 0)), mode='constant', constant_values=0)

################################
# preparing seed placement (assumed to be center of megastructure)
insertion_seed_array = np.arange(16) + 1
insertion_seed_array = np.pad(insertion_seed_array[:, np.newaxis], ((0, 0), (4, 0)), mode='edge')

center_seed_array = np.zeros((32, 32))
center_seed_array[8:24, 13:18] = insertion_seed_array

# as before, this prepares a padded version of the seed array
padded_center_seed_array = np.zeros((72, 34))
padded_center_seed_array[8 + 20:24 + 20, 13 + 1:18 + 1] = insertion_seed_array

################################
# Preparing the megastructure

#  control design - no invader system
M1 = Megastructure(slat_array, layer_interface_orientations=[2, (5, 2), 5])
M1.assign_crisscross_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
M1.assign_seed_handles(center_seed_array, center_seed_plate)
M1.patch_control_handles(core_plate)
if regenerate_graphics:
    M1.create_standard_graphical_report(os.path.join(output_folder, 'baseline_square_graphics'), colormap='Dark2')
    ################################

# Preparing invader design 1 (knock-in i.e. incumbent slat will be removed and replaced by the invader on the megastructure)
M_inv = Megastructure(padded_slat_array, layer_interface_orientations=[2, (5, 2), 5])
M_inv.assign_crisscross_handles(padded_handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
M_inv.assign_seed_handles(padded_center_seed_array, center_seed_plate)
# in this new version of the design, no cargo handles need to be added to the incumbent as they can all be placed on the invader instead
M_inv.patch_control_handles(core_plate)

if regenerate_graphics:
    M_inv.create_standard_graphical_report(os.path.join(output_folder, 'knock_in_incumbent_graphics'), colormap='Dark2')

# The actual invader for this design is simply the actual control y-slat, so a copy will be made here
# GNPs will also be added to the H5 side, for easier tracking
knock_in_invaders = []
for invader_number in range(8):
    knock_in_invader = copy.deepcopy(M1.slats['layer2-slat%s' % (17 + invader_number)])
    knock_in_invader.ID = 'INVADER %s' % (invader_number + 17)
    knock_in_invader.layer = 'FLOATING'
    knock_in_invader.slat_coordinates = 'N/A'
    for slat_position in range(1, 33):  # bart is codenamed with a 1 in this plate
        knock_in_invader.set_handle(slat_position, 5,
                                    simpsons_plate.get_sequence(slat_position, 5, 1),
                                    simpsons_plate.get_well(slat_position, 5, 1),
                                    simpsons_plate.get_plate_name(slat_position, 5, 1))
    knock_in_invaders.append(knock_in_invader)
################################
# Combining all slats together into the final echo protocol
full_slat_dict = {}

for i in range(8):
    full_slat_dict['KNOCK-IN INVADER %s' % (17 + i)] = knock_in_invaders[i]

for i in range(8):
    incumbent = copy.deepcopy(M_inv.slats['layer2-slat%s' % (17 + i)])
    incumbent.ID = 'KNOCK-IN INCUMBENT STRAND %s' % (17 + i)
    full_slat_dict['KNOCK-IN INCUMBENT STRAND %s' % (17 + i)] = incumbent

specific_plate_wells = plate96[0:8] + plate96[12:12 + 8]  # different groups are split into different rows for convenience
convert_slats_into_echo_commands(full_slat_dict, 'tmsd_test_plate',
                                 output_folder, 'all_echo_commands.csv',
                                 transfer_volume=150,
                                 specific_plate_wells=specific_plate_wells)
print(Fore.GREEN + 'Design complete, no errors found.')

####### PLOTTING VISUALIZATION
fig, ax = plt.subplots(figsize=(10, 10))
slatPadding = 0.25
rect_length = 32
for i in range(32):
    if i < 16 or i > 23:
        top_color = 'b'
    else:
        top_color = 'r'
    ax.add_patch(Rectangle((i, -slatPadding), 1 - 2 * slatPadding, rect_length, color=top_color, alpha=0.2))
    ax.add_patch(Rectangle((-slatPadding, i), rect_length, 1 - 2 * slatPadding, color='b', alpha=0.2))

# graph formatting
ax.set_ylim(-0.5, rect_length + 0.5)
ax.set_xlim(-0.5, rect_length + 0.5)
ax.invert_yaxis()  # y-axis is inverted to match the way the slats and patterns are numbered
plt.axis('off')
plt.savefig(os.path.join(output_folder, 'full_megastructure.png'), dpi=300)
plt.show()

fig, ax = plt.subplots(figsize=(10, 10))
slatPadding = 0.25
rect_length = 32
for i in range(32):
    if i < 16 or i > 23:
        top_color = 'b'
    else:
        top_color = 'r'
    if i not in [16, 17, 18, 19, 20, 21, 22, 23]:
        ax.add_patch(Rectangle((i, -slatPadding), 1 - 2 * slatPadding, rect_length, color=top_color, alpha=0.2))

    ax.add_patch(Rectangle((-slatPadding, i), rect_length, 1 - 2 * slatPadding, color='b', alpha=0.2))

# graph formatting
ax.set_ylim(-0.5, rect_length + 0.5)
ax.set_xlim(-0.5, rect_length + 0.5)
ax.invert_yaxis()  # y-axis is inverted to match the way the slats and patterns are numbered
plt.axis('off')
plt.savefig(os.path.join(output_folder, 'invader_megastructure.png'), dpi=300)
plt.show()
