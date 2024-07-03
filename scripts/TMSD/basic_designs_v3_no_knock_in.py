import numpy as np
import os
import copy
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from colorama import Fore

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.slat_design import generate_standard_square_slats, attach_cargo_handles_to_core_sequences
from crisscross.core_functions.hamming_functions import generate_handle_set_and_optimize, multi_rule_hamming
from crisscross.core_functions.slats import Slat

from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.plate_constants import (slat_core, core_plate_folder, assembly_handle_folder,
                                                         crisscross_h5_handle_plates, crisscross_h2_handle_plates,
                                                         seed_plug_plate_corner, seed_plug_plate_center,
                                                         cargo_plate_folder, nelson_quimby_antihandles)
from crisscross.plate_mapping import get_plateclass
from crisscross.helper_functions.plate_constants import plate96

########################################
# script setup
output_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/tmsd_demos/basic_square_tests_v3'
create_dir_if_empty(output_folder)
np.random.seed(8)
read_handles_from_file = True
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
########################################

########################################
# Shape generation and crisscross handle optimisation

slat_array, unique_slats_per_layer = generate_standard_square_slats(32)  # standard square
slat_invader_placement = 17  # this is the main slat involved in the TMSD circuit.  It is the 17th y-slat, starting from the left

# This is the 'invader' version of the design i.e. one slat is shifted up by 16 places to allow it to be invaded
padded_slat_array = np.pad(slat_array, ((20, 20), (1, 1), (0, 0)), mode='constant', constant_values=0)
padded_slat_array[padded_slat_array[..., 1] == slat_invader_placement, 1] = 0
padded_slat_array[4:36, slat_invader_placement, 1] = slat_invader_placement  # hard-coding of shift by 16

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
               delimiter=',',
               fmt='%i')

# This is a padded handle array to match the invader version of the design
padded_handle_array = np.pad(handle_array, ((20, 20), (1, 1), (0, 0)), mode='constant', constant_values=0)

########################################
# preparing seed placement (assumed to be center of megastructure)
insertion_seed_array = np.arange(16) + 1
insertion_seed_array = np.pad(insertion_seed_array[:, np.newaxis], ((0, 0), (4, 0)), mode='edge')

center_seed_array = np.zeros((32, 32))
center_seed_array[8:24, 13:18] = insertion_seed_array

# as before, this prepares a padded version of the seed array
padded_center_seed_array = np.zeros((72, 34))
padded_center_seed_array[8 + 20:24 + 20, 13 + 1:18 + 1] = insertion_seed_array

########################################
# Preparing the megastructure

#  control design - no invader system
M1 = Megastructure(slat_array, layer_interface_orientations=[2, (5, 2), 5])
M1.assign_crisscross_handles(handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
M1.assign_seed_handles(center_seed_array, center_seed_plate)
M1.patch_control_handles(core_plate)

######
# Preparing invader design 1 (knock-in i.e. incumbent slat will be removed and replaced by the invader on the megastructure)
M_inv = Megastructure(padded_slat_array, layer_interface_orientations=[2, (5, 2), 5])
M_inv.assign_crisscross_handles(padded_handle_array, crisscross_handle_x_plates, crisscross_antihandle_y_plates)
M_inv.assign_seed_handles(padded_center_seed_array, center_seed_plate)

# adds 16 Nelson handles to allow attachment of fluorescent strands (they are attached to the H2 side of the incumbent strand)
cargo_array = np.zeros(padded_slat_array.shape[0:2])
cargo_array[4:20, slat_invader_placement] = 3
M_inv.assign_cargo_handles(cargo_array, nelson_plate, 2, requested_handle_orientation=2)
M_inv.patch_control_handles(core_plate)

# The actual invader for this design is simply the actual control y-slat, so a copy will be made here
tmsd_slat_invader_1 = copy.deepcopy(M1.slats['layer2-slat%s' % slat_invader_placement])
tmsd_slat_invader_1.ID = 'INVADER 1 + control handle 17'
tmsd_slat_invader_1.layer = 'FLOATING'
tmsd_slat_invader_1.slat_coordinates = 'N/A'
######

# Preparing invader design 2 (knock-out i.e. incumbent strand is completely detached from the megastructure after invasion)
padded_handle_array_extended = np.copy(padded_handle_array)
padded_handle_array_extended[4:20, slat_invader_placement,
0] = 17  # the incumbent strand now needs handles to be able to 'hybridise'.  In this case I hard-coded them all to handle 17.  We can also consider hamming-optimizing this slat too.

M_inv_2 = Megastructure(padded_slat_array, layer_interface_orientations=[2, (5, 2), 5])
M_inv_2.assign_crisscross_handles(padded_handle_array_extended, crisscross_handle_x_plates,
                                  crisscross_antihandle_y_plates)
M_inv_2.assign_seed_handles(padded_center_seed_array, center_seed_plate)
M_inv_2.patch_control_handles(core_plate)

# for knock-out, the invader half-matches the actual control slat and half-matches the jutting-out slat (currently set entirely to handle 17)
# what is particularly important to note is that this time, the antihandles are flipped into handles as the invader is complementary to the y-slat itself instead
tmsd_slat_invader_2 = Slat('INVADER 2', 'FLOATING', 'N/A')

for slat_position in range(1, 33):
    if slat_position < 17:  # this is the first half of the invader, which matches the jutting out region of the incumbent
        tmsd_slat_invader_2.set_handle(slat_position, 5,
                                       crisscross_handle_x_plates.get_sequence(slat_position, 5, 17),
                                       crisscross_handle_x_plates.get_well(slat_position, 5, 17),
                                       crisscross_handle_x_plates.get_plate_name(slat_position, 5, 17))
    else:  # this is the second half of the invader, matching the specific assembly handles of the megastructure, which I get from the original handle array
        tmsd_slat_invader_2.set_handle(slat_position, 5,
                                       crisscross_handle_x_plates.get_sequence(slat_position, 5, handle_array[
                                           slat_position - 17, slat_invader_placement - 1, 0]),
                                       crisscross_handle_x_plates.get_well(slat_position, 5, handle_array[
                                           slat_position - 17, slat_invader_placement - 1, 0]),
                                       crisscross_handle_x_plates.get_plate_name(slat_position, 5, handle_array[
                                           slat_position - 17, slat_invader_placement - 1, 0]))

    # full anti-Nelson H2 layer is included to allow for fluorophore handles to be attached
    tmsd_slat_invader_2.set_handle(slat_position, 2,
                                   nelson_plate.get_sequence(slat_position, 2, 3),
                                   nelson_plate.get_well(slat_position, 2, 3),
                                   nelson_plate.get_plate_name(slat_position, 2, 3))
################################
# Combining all slats together into the final echo protocol
full_slat_dict = {}
for key, slat in M1.slats.items():
    if 'layer1' in key:  # X-slats are consistent for all designs
        full_slat_dict[key] = slat
    elif int(key.split('slat')[-1]) < slat_invader_placement or int(key.split('slat')[
                                                                        -1]) > 24:  # The first 16 Y-slats are also consistent for all designs, as well as the final 8 slats
        full_slat_dict[key] = slat

# the next 8 slats in the list include the remaining control y handles, of which the first one actually also doubles as the first invader slat
full_slat_dict['INVADER 1 + control handle 17'] = tmsd_slat_invader_1
for i in range(7):
    full_slat_dict['layer2-slat%s' % (slat_invader_placement + 1 + i)] = M1.slats[
        'layer2-slat%s' % (slat_invader_placement + 1 + i)]

# finally, the next 2 slats include the incumbent knock-out slat as well as the corresponding invader slat
full_slat_dict['INCUMBENT STRAND 2'] = M_inv_2.slats['layer2-slat%s' % slat_invader_placement]
full_slat_dict['INCUMBENT STRAND 2'].ID = 'INCUMBENT STRAND 2'
full_slat_dict['INVADER 2'] = tmsd_slat_invader_2

specific_plate_wells = plate96[0:32] + plate96[36:36 + 24] + plate96[60:60 + 8] + plate96[72:72+2] # different groups are split into different rows for convenience
all_transfer_volumes = [75] * (32+24) + [150] * (8 + 2)

convert_slats_into_echo_commands(full_slat_dict, 'tmsd_test_plate',
                                 output_folder, 'all_echo_commands.csv',
                                 transfer_volume=all_transfer_volumes,
                                 specific_plate_wells=specific_plate_wells)

print (Fore.GREEN + 'Design complete, no errors found.')

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
    if i != 16:
        ax.add_patch(Rectangle((i, -slatPadding), 1 - 2 * slatPadding, rect_length, color=top_color, alpha=0.2))

    ax.add_patch(Rectangle((-slatPadding, i), rect_length, 1 - 2 * slatPadding, color='b', alpha=0.2))

# graph formatting
ax.set_ylim(-0.5, rect_length + 0.5)
ax.set_xlim(-0.5, rect_length + 0.5)
ax.invert_yaxis()  # y-axis is inverted to match the way the slats and patterns are numbered
plt.axis('off')
plt.savefig(os.path.join(output_folder, 'invader_megastructure.png'), dpi=300)
plt.show()
