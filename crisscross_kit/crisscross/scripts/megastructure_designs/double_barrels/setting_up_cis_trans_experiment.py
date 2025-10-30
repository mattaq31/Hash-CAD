import os
import copy
from math import floor
from collections import OrderedDict

from crisscross.core_functions.megastructures import Megastructure

# this file is meant to transplant all assembly handles from the evolved CisTrans design into a file that contains
# all slat variants that will be tested experimentally, included knockout patterns to test spurious nucleation problems

########## CONFIG
# update these depending on user
experiment_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Crisscross Designs/MAD-C13 Chirality with CisTrans'

evolved_handles_design = os.path.join(experiment_folder, 'CisTrans optimized.xlsx')
all_components_design = os.path.join(experiment_folder, 'CisTrans all options.xlsx')

########## LOADING DESIGNS

mega_evo = Megastructure(import_design_file=evolved_handles_design)
mega_all = Megastructure(import_design_file=all_components_design)

########## TRANSPLANTING
# STEP 1: TRANSPLANT L1 HANDLES
print('transplanting layer 1 handles from evolved design to all options design...')

for slat_id in range(1,17):
    slat_name = 'layer1-slat%s' % slat_id
    input_slat = mega_evo.slats[slat_name]

    # this automatically sets both L and R variants in their correct chirality
    for t in [slat_id, slat_id + 16]:
        target_slat_name = 'layer1-slat%s' % t
        target_slat = mega_all.slats[target_slat_name]
        target_slat.H5_handles = copy.deepcopy(input_slat.H5_handles)

    #  step 2: assigns handles to replacement standard slats
    for ordered_handle_index, handle in enumerate(range(17, 33)):
        target_slat = mega_all.slats['layer2-slat%s' % (16 - ordered_handle_index)]
        target_slat.H2_handles[slat_id + 8] = copy.copy(input_slat.H5_handles[handle])

# STEP 3: TRANSPLANT L2 KNOCKOUT HANDLES
print('transplanting layer 2 handles from evolved design to all options design...')

for slat_id in range(24, 8, -1):
    slat_name = 'layer2-slat%s' % slat_id
    input_slat = mega_evo.slats[slat_name]

    # sets both slat arms at once
    for t in [slat_id + 8, slat_id + 40]:
        target_slat_name = 'layer2-slat%s' % t
        target_slat = mega_all.slats[target_slat_name]
        target_slat.H5_handles = copy.deepcopy(input_slat.H5_handles)
        # knockout handles to limit DB spurious nucleation events
        for handle in range(17, 33):
            if handle % 2 == 0 and slat_id % 2 == 0:
                target_slat.remove_handle(handle, 5)
            elif handle % 2 == 1 and slat_id % 2 == 1:
                target_slat.remove_handle(handle, 5)

# sets same H2 pattern for the other DB pattern types on layer 3
for slat_index, slat_id in enumerate(range(32, 16, -1)):
    slat_name = 'layer2-slat%s' % slat_id
    input_slat = mega_all.slats[slat_name]
    for ordered_handle_index, handle in enumerate(range(17, 33)):
        if handle in input_slat.H5_handles:
            for base_target_slat in [25, 33, 41]:
                target_slat = mega_all.slats['layer3-slat%s' % (base_target_slat + floor(ordered_handle_index/2))]
                if handle % 2 == 0:
                    target_slat.H2_handles[32 - slat_index] = copy.copy(input_slat.H5_handles[handle])
                else:
                    target_slat.H2_handles[1 + slat_index] = copy.copy(input_slat.H5_handles[handle])

# sets same H2 pattern for the other DB pattern types on layer 5
for slat_index, slat_id in enumerate(range(64, 48, -1)):
    slat_name = 'layer2-slat%s' % slat_id
    input_slat = mega_all.slats[slat_name]
    for ordered_handle_index, handle in enumerate(range(17, 33)):
        if handle in input_slat.H5_handles:
            for base_target_slat in [17, 25, 33, 41]:
                target_slat = mega_all.slats['layer5-slat%s' % (base_target_slat + floor(ordered_handle_index/2))]
                if handle % 2 == 0:
                    target_slat.H2_handles[32 - slat_index] = copy.copy(input_slat.H5_handles[handle])
                else:
                    target_slat.H2_handles[1 + slat_index] = copy.copy(input_slat.H5_handles[handle])

# STEP 4: TRANSPLANT L3 KNOCKOUT HANDLES
print('transplanting layer 3 handles from evolved design to all options design...')

# given the pattern is irregular, did not try to develop a systematic way to generate these patterns, just hardcoded them
pattern_2_reject_1 = [2, 5, 8, 11, 14, 16, 18, 21, 24, 27, 30]
pattern_2_reject_2 = [3, 6, 9, 12, 15, 16, 20, 23, 26, 29, 32]
pattern_2_reject_3 = [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31]
pattern_2_reject_4 = [2, 4, 5, 8, 10,11, 14, 16, 18, 20, 21, 24, 26, 27, 30, 32]
pattern_2_reject_5 = [2, 3, 6, 8, 9, 12, 15, 16, 19, 20, 22, 23, 26, 28, 29, 32]
pattern_2_reject_6 = [1, 4, 7,10, 13, 16, 19, 22, 25, 28, 31]

pattern_2_rejects = {
    1: pattern_2_reject_1,
    2: pattern_2_reject_2,
    3: pattern_2_reject_3,
    4: pattern_2_reject_4,
    5: pattern_2_reject_5,
    6: pattern_2_reject_6
}
pattern_2_rejects_rhs = {}

rhs_id_mapping = { # this just maps how the LHS and RHS patterns relate, I think this is a flipping operation...
    2: 1,
    1: 2,
    3: 3,
    5: 4,
    4: 5,
    6: 6
}

# otherwise, patterns can be flipped by reversing the sequence
for id, pattern in pattern_2_rejects.items():
    pattern_2_rejects_rhs[rhs_id_mapping[id]] = [33 - p for p in pattern[::-1]]

pattern_3_odd_reject = [4, 8, 12, 16, 19, 23, 27, 31]
pattern_3_even_reject = [1, 5, 9, 13, 16, 18, 22, 26, 30]

# ditto for pattern 3
pattern_3_odd_reject_rhs = [33 - p for p in pattern_3_even_reject]
pattern_3_even_reject_rhs = [33 - p for p in pattern_3_odd_reject]

for slat_index, slat_id in enumerate(range(8, 0, -1)):
    slat_name = 'layer3-slat%s' % slat_id
    slat_name_rhs = 'layer5-slat%s' % slat_id
    input_slat = mega_evo.slats[slat_name]
    input_slat_rhs = mega_evo.slats[slat_name_rhs]

    # handles transplanted here, and then knockout in specific patterns as required
    for slat_group_index, t in enumerate([slat_id + 16, slat_id + 24, slat_id + 32, slat_id + 40]):
        target_slat_name = 'layer3-slat%s' % t
        target_slat_name_rhs = 'layer5-slat%s' % t

        target_slat = mega_all.slats[target_slat_name]
        target_slat_rhs = mega_all.slats[target_slat_name_rhs]

        target_slat.H5_handles = copy.deepcopy(input_slat.H5_handles)
        target_slat_rhs.H5_handles = copy.deepcopy(input_slat_rhs.H5_handles)

        for handle in range(1, 33):
            if slat_group_index == 1:
                if handle % 2 == 0:
                    target_slat.remove_handle(handle, 5)
                else:
                    target_slat_rhs.remove_handle(handle, 5)
            elif slat_group_index == 2:
                selected_pattern = (slat_index % 6) + 1
                if handle in pattern_2_rejects[selected_pattern]:
                    target_slat.remove_handle(handle, 5)
                if handle in pattern_2_rejects_rhs[selected_pattern]:
                    target_slat_rhs.remove_handle(handle, 5)

            elif slat_group_index == 3:
                if slat_id % 2 == 0:
                    if handle in pattern_3_even_reject:
                        target_slat.remove_handle(handle, 5)
                    if handle in pattern_3_even_reject_rhs:
                        target_slat_rhs.remove_handle(handle, 5)
                else:
                    if handle in pattern_3_odd_reject:
                        target_slat.remove_handle(handle, 5)
                    if handle in pattern_3_odd_reject_rhs:
                        target_slat_rhs.remove_handle(handle, 5)

# STEP 4: TRANSPLANT L4 HANDLES AND IMPLEMENT KNOCKOUTS
print('transplanting layer 4 handles from evolved design to all options design...')

for slat_id in range(9,25):
    slat_name = 'layer3-slat%s' % slat_id
    slat_name_rhs = 'layer5-slat%s' % slat_id
    input_slat = mega_evo.slats[slat_name]
    input_slat_rhs = mega_evo.slats[slat_name_rhs]

    for t in [slat_id-8]:
        target_slat_name = 'layer3-slat%s' % t
        target_slat_name_rhs = 'layer5-slat%s' % t
        target_slat = mega_all.slats[target_slat_name]
        target_slat_rhs = mega_all.slats[target_slat_name_rhs]
        target_slat.H5_handles = copy.deepcopy(input_slat.H5_handles)
        target_slat_rhs.H5_handles = copy.deepcopy(input_slat_rhs.H5_handles)
        # knockout handles to limit DB spurious nucleation events
        for handle in range(17, 33):
            if handle % 2 == 0 and slat_id % 2 == 0:
                target_slat.remove_handle(handle, 5)
                target_slat_rhs.remove_handle(handle, 5)
            elif handle % 2 == 1 and slat_id % 2 == 1:
                target_slat.remove_handle(handle, 5)
                target_slat_rhs.remove_handle(handle, 5)

########## DBL PURIFICATION HANDLES
print('adding double purification handles...')
for slat_id in [list(range(17, 33)), list(range(49, 65))]:
    for s_id in slat_id:
        slat_name = 'layer2-slat%s' % s_id
        target_slat = mega_all.slats[slat_name]
        target_slat.set_placeholder_handle(32, 2, 'CARGO', 'SSW041DoublePurification5primetoehold',
                                           descriptor='Placeholder|Cargo|SSW041DoublePurification5primetoehold')

####### final double barrel knockouts

print('finalizing double barrel knockouts...')
slat_array = mega_all.generate_slat_occupancy_grid()
handle_array = mega_all.generate_assembly_handle_grid()

# there is a single slat (layer1-slat16) that should not have its handles knocked out, since it'll be used for three different layer 2 groups which need various combinations of handles
# so instead, I'll create a copy of it (layer1-slat33) and place it in the design, which can then be used to substitute for layer1-slat16 in the echo file generation
original_full_slat = copy.deepcopy(mega_all.slats['layer1-slat16'])
original_full_slat.ID = 'layer1-slat33'
new_pos_to_coord = OrderedDict()
new_coord_to_pos = OrderedDict()
for coordinate, position in original_full_slat.slat_coordinate_to_position.items():
    new_pos_to_coord[position] = (93, 31 + position)
    new_coord_to_pos[(93, 31 + position)] = position

original_full_slat.slat_coordinate_to_position = new_coord_to_pos
original_full_slat.slat_position_to_coordinate = new_pos_to_coord
original_full_slat.H2_handles = {}
mega_all.slats['layer1-slat33'] = original_full_slat

for slat_id, slat in mega_all.slats.items():
    if slat.slat_type == 'DB-R':
        slat.remove_handle(17, 5)
        handle_coord = slat.slat_position_to_coordinate[17]
        if slat.layer != len(mega_all.layer_palette):
            opposing_slat_id = slat_array[handle_coord[0], handle_coord[1], slat.layer]
            if opposing_slat_id != 0: # TODO: would be good to add this as a function within the megastructure class
                opposing_slat = mega_all.slats[f'layer{slat.layer + 1}-slat{opposing_slat_id}']
                opposing_handle = opposing_slat.slat_coordinate_to_position[handle_coord]
                opposing_slat.remove_handle(opposing_handle, 2)

        if slat.layer == 2:
            slat.remove_handle(17, 2)
            opposing_slat_id = slat_array[handle_coord[0], handle_coord[1], slat.layer - 2]
            if opposing_slat_id != 0:
                opposing_slat = mega_all.slats[f'layer{slat.layer - 1}-slat{opposing_slat_id}']
                opposing_handle = opposing_slat.slat_coordinate_to_position[handle_coord]
                opposing_slat.remove_handle(opposing_handle, 5)

    if slat.slat_type == 'DB-L':
        slat.remove_handle(16, 5)
        handle_coord = slat.slat_position_to_coordinate[16]
        if slat.layer != len(mega_all.layer_palette):
            opposing_slat_id = slat_array[handle_coord[0], handle_coord[1], slat.layer]
            if opposing_slat_id != 0: # TODO: would be good to add this as a function within the megastructure class
                opposing_slat = mega_all.slats[f'layer{slat.layer + 1}-slat{opposing_slat_id}']
                opposing_handle = opposing_slat.slat_coordinate_to_position[handle_coord]
                opposing_slat.remove_handle(opposing_handle, 2)

        if slat.layer == 2:
            slat.remove_handle(16, 2)
            opposing_slat_id = slat_array[handle_coord[0], handle_coord[1], slat.layer - 2]
            if opposing_slat_id != 0:
                opposing_slat = mega_all.slats[f'layer{slat.layer - 1}-slat{opposing_slat_id}']
                opposing_handle = opposing_slat.slat_coordinate_to_position[handle_coord]
                opposing_slat.remove_handle(opposing_handle, 5)

########## EXPORT
mega_all.export_design('CisTrans all options with assembly handles.xlsx', experiment_folder)

