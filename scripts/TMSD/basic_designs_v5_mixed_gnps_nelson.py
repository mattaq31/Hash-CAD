import numpy as np
import os
import copy
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from colorama import Fore

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.assembly_handle_optimization.hamming_compute import multirule_precise_hamming
from crisscross.assembly_handle_optimization.random_hamming_optimizer import generate_handle_set_and_optimize
from crisscross.core_functions.slats import Slat

from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.plate_constants import cargo_plate_folder, nelson_quimby_antihandles, octahedron_patterning_v1
from crisscross.plate_mapping import get_plateclass, get_standard_plates
from crisscross.helper_functions.plate_constants import plate96

################################
# script setup
output_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/tmsd_demos/basic_square_tests_v5'
create_dir_if_empty(output_folder)
np.random.seed(8)
read_handles_from_file = True
regenerate_graphics = False
################################
# Plate sequences
core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate = get_standard_plates()
nelson_plate = get_plateclass('GenericPlate', nelson_quimby_antihandles, cargo_plate_folder)
bart_plate = get_plateclass('GenericPlate', octahedron_patterning_v1, cargo_plate_folder)
cargo_key = {3: 'antiNelson', 1: 'antiBart', 2: 'antiEdna'}
################################

################################
# Shape generation and crisscross handle optimisation

slat_array, unique_slats_per_layer = generate_standard_square_slats(32)  # standard square
slat_invader_placement = 18  # this slat has been changed to 18, to allow for the inclusion of a trench on either side of the slat

# This is the 'invader' version of the design i.e. one slat is shifted up by 16 places to allow it to be invaded
padded_slat_array = np.pad(slat_array, ((20, 20), (1, 1), (0, 0)), mode='constant', constant_values=0)
padded_slat_array[padded_slat_array[..., 1] == slat_invader_placement, 1] = 0
padded_slat_array[4:36, slat_invader_placement, 1] = slat_invader_placement

# assembly handle optimization (currently reading in design from crossbar megastructure)
if read_handles_from_file:
    handle_array = np.loadtxt(os.path.join(output_folder, 'optimized_handle_array.csv'), delimiter=',').astype(
        np.float32)
    handle_array = handle_array[..., np.newaxis]
    result = multirule_precise_hamming(slat_array, handle_array)
    print('Hamming distance from file-loaded design: %s' % result['Universal'])
else:
    handle_array = generate_handle_set_and_optimize(slat_array, unique_sequences=32, max_rounds=150)
    np.savetxt(os.path.join(output_folder, 'optimized_handle_array.csv'), handle_array.squeeze().astype(np.int32),
               delimiter=',',
               fmt='%i')

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

# adds 10 Nelson handles to allow attachment of fluorescent strands (they are attached to the H2 side of the incumbent strand)
# also adds 6 Bart handles to allow attachment of GNPs for tracking the construct via TEM
cargo_array = np.zeros(padded_slat_array.shape[0:2])
cargo_array[4:20, slat_invader_placement] = 3
cargo_array[5:7, slat_invader_placement] = 0
cargo_array[11:13, slat_invader_placement] = 0
cargo_array[17:19, slat_invader_placement] = 0

cargo_array_2 = np.zeros(padded_slat_array.shape[0:2])
cargo_array_2[5:7, slat_invader_placement] = 1
cargo_array_2[11:13, slat_invader_placement] = 1
cargo_array_2[17:19, slat_invader_placement] = 1

M_inv.assign_cargo_handles_with_array(cargo_array, cargo_key, nelson_plate, 2, handle_orientation=2)
M_inv.assign_cargo_handles_with_array(cargo_array_2, cargo_key, bart_plate, 2, handle_orientation=2)

M_inv.patch_control_handles(core_plate)

if regenerate_graphics:
    M_inv.create_standard_graphical_report(os.path.join(output_folder, 'knock_in_incumbent_graphics'), colormap='Dark2')

# The actual invader for this design is simply the actual control y-slat, so a copy will be made here
tmsd_slat_invader_1 = copy.deepcopy(M1.slats['layer2-slat%s' % slat_invader_placement])
tmsd_slat_invader_1.ID = 'INVADER 1 + control handle 17'
tmsd_slat_invader_1.layer = 'FLOATING'
tmsd_slat_invader_1.slat_coordinates = 'N/A'

################################
# Preparing invader design 2 (knock-out i.e. incumbent strand is completely detached from the megastructure after invasion)
padded_handle_array_extended = np.copy(padded_handle_array)
padded_handle_array_extended[4:20, slat_invader_placement, 0] = 17  # the incumbent strand now needs handles to be able to 'hybridise'.  In this case I hard-coded them all to handle 17.  We can also consider hamming-optimizing this slat too.
M_inv_2 = Megastructure(padded_slat_array, layer_interface_orientations=[2, (5, 2), 5])
M_inv_2.assign_crisscross_handles(padded_handle_array_extended, crisscross_handle_x_plates,
                                  crisscross_antihandle_y_plates)
M_inv_2.assign_seed_handles(padded_center_seed_array, center_seed_plate)
M_inv_2.patch_control_handles(core_plate)
if regenerate_graphics:
    M_inv_2.create_standard_graphical_report(os.path.join(output_folder, 'knock_out_incumbent_graphics'), colormap='Dark2')

# for knock-out, the invader half-matches the actual control slat and half-matches the jutting-out slat (currently set entirely to handle 18)
# what is particularly important to note is that this time, the antihandles are flipped into handles as the invader is complementary to the y-slat itself instead

tmsd_slat_invader_2 = Slat('INVADER 2-16', 'FLOATING', 'N/A')

# I added a second invader to this design so we can test a more strongly-bound incumbent strand too
tmsd_slat_invader_2_24 = Slat('INVADER 2-24', 'FLOATING', 'N/A')

for sel_invader_slat in [tmsd_slat_invader_2, tmsd_slat_invader_2_24]:
    if sel_invader_slat.ID == 'INVADER 2-16':
        slat_binding_start = 17
    else:
        slat_binding_start = 9
    for slat_position in range(1, 33):
        if slat_position < slat_binding_start:  # this is the first half of the invader, which matches the jutting out region of the incumbent
            sel_invader_slat.set_handle(slat_position, 5,
                                        crisscross_handle_x_plates.get_sequence(slat_position, 5, 17),
                                        crisscross_handle_x_plates.get_well(slat_position, 5, 17),
                                        crisscross_handle_x_plates.get_plate_name(slat_position, 5, 17),
                                        descriptor='Ass. Handle %s, Plate %s' % (17, crisscross_handle_x_plates.get_plate_name(slat_position, 5, 17)))
        else:  # this is the second half of the invader, matching the specific assembly handles of the megastructure, which I get from the original handle array
            handle_val = handle_array[slat_position - slat_binding_start, slat_invader_placement - 1, 0]
            sel_invader_slat.set_handle(slat_position, 5,
                                        crisscross_handle_x_plates.get_sequence(slat_position, 5, handle_val),
                                        crisscross_handle_x_plates.get_well(slat_position, 5, handle_val),
                                        crisscross_handle_x_plates.get_plate_name(slat_position, 5, handle_val),
                                        descriptor='Ass. Handle %s, Plate %s' % (handle_val, crisscross_handle_x_plates.get_plate_name(slat_position, 5, handle_val)))

        #  anti-Nelson H2 layer is included to allow for fluorophore handles to be attached
        # 10 bart handles are also attached to allow for GNP screening too
        if slat_position in [2, 3, 8, 9, 14, 15, 20, 21, 26, 27]:
            sel_invader_slat.set_handle(slat_position, 2,
                                        bart_plate.get_sequence(slat_position, 2, 1),
                                        bart_plate.get_well(slat_position, 2, 1),
                                        bart_plate.get_plate_name(slat_position, 2, 1))
        else:
            sel_invader_slat.set_handle(slat_position, 2,
                                        nelson_plate.get_sequence(slat_position, 2, 3),
                                        nelson_plate.get_well(slat_position, 2, 3),
                                        nelson_plate.get_plate_name(slat_position, 2, 3))

# the incumbent strand for the second invader is built below:
incumbent_2_24_posns = copy.deepcopy(M_inv_2.slats['layer2-slat%s' % slat_invader_placement])
incumbent_2_24_posns.ID = 'INCUMBENT STRAND 2-24'
for j in range(24):
    handle_val = handle_array[j, slat_invader_placement - 1, 0]
    incumbent_2_24_posns.set_handle(9 + j, 2,
                                    crisscross_antihandle_y_plates.get_sequence(9 + j, 2, handle_val),
                                    crisscross_antihandle_y_plates.get_well(9 + j, 2, handle_val),
                                    crisscross_antihandle_y_plates.get_plate_name(9 + j, 2, handle_val),
                                    descriptor='Ass. Handle %s, Plate %s' % (handle_val, crisscross_antihandle_y_plates.get_plate_name(9 + j, 2, handle_val)))
################################
# Combining all slats together into the final echo protocol
full_slat_dict = {}
for key, slat in M1.slats.items():
    if 'layer1' in key:  # X-slats are consistent for all designs
        full_slat_dict[key] = slat
    elif int(key.split('slat')[-1]) < 17 or int(key.split('slat')[-1]) > 24:  # The first 16 Y-slats are also consistent for all designs, as well as the final 8 slats
        full_slat_dict[key] = slat

# the next 8 slats in the list include the remaining control y handles, of which the second one actually also doubles as the first invader slat
for i in range(8):
    if i == 1:
        full_slat_dict['INVADER 1 + control handle 18'] = tmsd_slat_invader_1
    else:
        full_slat_dict['layer2-slat%s' % (slat_invader_placement - 1 + i)] = M1.slats[
            'layer2-slat%s' % (slat_invader_placement - 1 + i)]

# For this design, we are also going to include one knock-in incumbent strand, just to be able to test if this process works
full_slat_dict['INCUMBENT STRAND 1'] = M_inv.slats['layer2-slat%s' % slat_invader_placement]
full_slat_dict['INCUMBENT STRAND 1'].ID = 'INCUMBENT STRAND 1'

# The next 2 slats include the incumbent knock-out slat as well as the corresponding invader slat
full_slat_dict['INCUMBENT STRAND 2-16'] = M_inv_2.slats['layer2-slat%s' % slat_invader_placement]
full_slat_dict['INCUMBENT STRAND 2-16'].ID = 'INCUMBENT STRAND 2-16'
full_slat_dict['INVADER 2-16'] = tmsd_slat_invader_2

# Finally, the last 2 slats are the new extended slats for the 24-handle knock-out design
full_slat_dict['INCUMBENT STRAND 2-24'] = incumbent_2_24_posns
full_slat_dict['INVADER 2-24'] = tmsd_slat_invader_2_24

specific_plate_wells = plate96[0:32] + plate96[36:36 + 24] + plate96[60:60 + 8] + plate96[72:72 + 1] + plate96[84:84 + 4]  # different groups are split into different rows for convenience
all_transfer_volumes = [75] * (32 + 24) + [150] * (8 + 5)

convert_slats_into_echo_commands(full_slat_dict, 'tmsd_test_plate',
                                 output_folder, 'all_echo_commands.csv',
                                 default_transfer_volume=all_transfer_volumes,
                                 manual_plate_well_assignments=specific_plate_wells)

extension_slats = {}
for slat_key in ['INCUMBENT STRAND 1', 'INCUMBENT STRAND 2-16', 'INVADER 2-16', 'INCUMBENT STRAND 2-24', 'INVADER 2-24']:
    extension_slats[slat_key] = full_slat_dict[slat_key]

convert_slats_into_echo_commands(extension_slats, 'tmsd_test_plate',
                                 output_folder, 'specific_extension_echo_commands.csv',
                                 default_transfer_volume=150)

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
    if i not in [16, 17, 18]:
        ax.add_patch(Rectangle((i, -slatPadding), 1 - 2 * slatPadding, rect_length, color=top_color, alpha=0.2))

    ax.add_patch(Rectangle((-slatPadding, i), rect_length, 1 - 2 * slatPadding, color='b', alpha=0.2))

# graph formatting
ax.set_ylim(-0.5, rect_length + 0.5)
ax.set_xlim(-0.5, rect_length + 0.5)
ax.invert_yaxis()  # y-axis is inverted to match the way the slats and patterns are numbered
plt.axis('off')
plt.savefig(os.path.join(output_folder, 'invader_megastructure.png'), dpi=300)
plt.show()
