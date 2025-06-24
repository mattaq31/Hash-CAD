from crisscross.helper_functions import create_dir_if_empty
from crisscross.plate_mapping.plate_constants import *
import os
from crisscross.core_functions.plate_handling import read_dna_plate_mapping, export_standardized_plate_sheet
from crisscross.plate_mapping.non_standard_plates.plate_concentrations import concentration_library
import math
import string


def apply_name_update(category, side, position, cargo_id, sp_name, plate, index):
    """
    Helper function to apply the new name and description to the plate DataFrame.
    """
    new_key = f'{category}-{cargo_id}-{side}-{position}'
    if category == 'SEED':
        new_description = f'Seed Handle For Slat Position {position.split("_")[-1]}, Side {side}, {sp_name} Seed ID {seed_id}'
    elif 'ASSEMBLY' in category:
        new_description = f'{string.capwords(category.replace("_", " "))} For Slat Position {position.split("_")[-1]}, Side {side}, Sequence ID {cargo_id}'
    elif 'FLAT' in category:
        new_description = f'Flat Staple For Slat Position {position.split("_")[-1]}, Side {side}'
    elif 'CARGO' in category:
        new_description = f'Cargo Handle For Slat Position {position.split("_")[-1]}, Side {side}, Cargo ID {cargo_id}'

    plate.at[index, 'name'] = new_key
    plate.at[index, 'description'] = new_description

seed_plates = [seed_plug_plate_center, seed_plug_plate_corner,
               seed_plug_plate_all, seed_plug_plate_center_8064,
               seed_plug_plate_all_8064]

seed_plate_types = ['center', 'corner', 'all', 'center_8064', 'all_8064']
main_folder = '/Users/matt/Desktop/hash_cad_plates'
output_folder = os.path.join(main_folder, 'seed_plates')
create_dir_if_empty(output_folder)

# SEED PREPARATION
for sp, tp in zip(seed_plates, seed_plate_types):
    sp_name = '_'.join(sp.split('_')[0:2])
    full_file = os.path.join(old_core_folder, sp + '.xlsx')
    print(sp_name)
    plate = read_dna_plate_mapping(full_file, data_type='2d_excel', plate_size=384).reset_index(drop=True)

    if 'all' in tp or '8064' in tp:
        for ind, pattern in enumerate(plate['name'].tolist()):
            name_key = pattern.split('_')
            side = name_key[1]
            slat_position = name_key[2].replace('-', '_')
            slat_position_int = int(slat_position.split('_')[1])
            if slat_position_int > 10:
                slat_position_int -= 13
            seed_id = f'{slat_position_int}_{name_key[0].split("-")[-1]}'
            apply_name_update('SEED', side, slat_position, seed_id,  '8064' if '8064' in sp else '8634', plate, ind)
        if '3621' in sp_name:
            plate['concentration'] = 200
        else:
            plate['concentration'] = 500

    elif 'corner' in tp:
        position_tracker = 1
        for ind, pattern in enumerate(plate['description'].str.extract(r'(x-\d+-n\d+)', expand=False).tolist()):
            if isinstance(pattern, float) and math.isnan(pattern):
                continue
            key = (int(pattern.split('-')[2][1:]) + 1, 2, int(pattern.split('-')[1]))
            seed_id = f'{key[0]}_{key[2]}'
            apply_name_update('SEED', 'h'+str(key[1]), 'position_' + str(key[0]), seed_id,  '8064' if '8064' in sp else '8634', plate, ind)
        plate['concentration'] = 500
    else: # center remains
        position_tracker = 1
        plate['concentration'] = 500
        for ind, pattern in enumerate(plate['name'].tolist()):
            if 'Oligo' in pattern:
                plate.at[ind, 'name'] = 'NON-SLAT OLIGO'
                plate.at[ind, 'concentration'] = 0
                continue
            key = (int(pattern.split('.')[0][1:]) + 1, 2, position_tracker)
            if key[0] == 18:
                position_tracker += 1
            seed_id = f'{key[0]-13}_{key[2]}'
            apply_name_update('SEED', 'h' + str(key[1]), 'position_' + str(key[0]), seed_id, '8064' if '8064' in sp else '8634', plate, ind)


    export_standardized_plate_sheet(plate, output_folder, sp + '.xlsx')
print('SEED PLATES COMPLETE')

output_folder = os.path.join(main_folder, 'assembly_plates')
create_dir_if_empty(output_folder)

all_ass_plates = cckz_h2_antihandle_plates + cckz_h5_handle_plates + cckz_h5_sample_handle_plates + cckz_h2_sample_antihandle_plates + crisscross_h2_handle_plates + crisscross_h5_handle_plates
ass_sides = ['h2'] * 6 + ['h5'] * 6 + ['h5'] * 3 + ['h2'] * 3 + ['h2'] * 3 + ['h5'] * 6
ass_categories = ['ASSEMBLY_ANTIHANDLE'] * 6 + ['ASSEMBLY_HANDLE'] * 6 + ['ASSEMBLY_HANDLE'] * 3 + ['ASSEMBLY_ANTIHANDLE'] * 3 + ['ASSEMBLY_ANTIHANDLE'] * 3 + ['ASSEMBLY_HANDLE'] * 3 + ['ASSEMBLY_ANTIHANDLE'] * 3
ass_versions = ['v2'] * 6 + ['v2'] * 6 + ['v2'] * 3 + ['v2'] * 3 + ['v1'] * 3 + ['v1'] * 6

# ASSEMBLY HANDLE PREPARATION
for ass_plate, h_side, category, version in zip(all_ass_plates, ass_sides, ass_categories, ass_versions):
    sp_name = '_'.join(ass_plate.split('_')[0:2])
    full_file = os.path.join(old_assembly_folder, ass_plate + '.xlsx')
    print(sp_name)
    plate = read_dna_plate_mapping(full_file, data_type='2d_excel', plate_size=384).reset_index(drop=True)

    for ind, pattern in enumerate(plate['description'].str.extract(r'(n\d+_k\d+)', expand=False)):
        if isinstance(pattern, float) and math.isnan(pattern):
            continue
        slat_position = int(pattern.split('_k')[0][1:]) + 1
        assembly_handle_id = int(pattern.split('_k')[1])
        apply_name_update(category + '_' + version, h_side, 'position_' + str(slat_position), assembly_handle_id, '', plate, ind)

    if ass_plate in cckz_h5_sample_handle_plates or ass_plate in cckz_h2_sample_antihandle_plates:
        plate['concentration'] = 100
    else:
        plate['concentration'] = 500

    if sp_name == 'P3601_MA':
        plate.loc[plate['well'].isin(['N19', 'N22', 'N24']), 'concentration'] = 50

    export_standardized_plate_sheet(plate, output_folder, ass_plate + '.xlsx')

print('ASSEMBLY PLATES COMPLETE')

# FLAT STAPLE PREPARATION
output_folder = os.path.join(main_folder, 'flat_staple_plates')
create_dir_if_empty(output_folder)

for c_plate in [slat_core, slat_core_latest]:
    sp_name = '_'.join(c_plate.split('_')[0:2])
    full_file = os.path.join(old_core_folder, c_plate + '.xlsx')
    print(sp_name)
    plate = read_dna_plate_mapping(full_file, data_type='2d_excel', plate_size=384).reset_index(drop=True)
    plate['concentration'] = 500
    if sp_name == 'sw_src002':
        for ind, pattern in enumerate(plate['name'].str.extract(r'(\d+-h\d)', expand=False)):
            if isinstance(pattern, float) and math.isnan(pattern):
                plate.at[ind, 'name'] = 'NON-SLAT OLIGO'
                plate.at[ind, 'concentration'] = 0
                continue
            slat_side = int(pattern.split('-')[1][1])
            if slat_side == 5:
                slat_position = int(pattern.split('-')[0]) -32
            else:
                slat_position = int(pattern.split('-')[0])
            apply_name_update('FLAT', 'h' + str(slat_side), 'position_' + str(slat_position), 'BLANK', '', plate, ind)
    else:
        for ind, pattern in enumerate(plate['name'].tolist()):
            slat_side = int(pattern.split('_')[1][1])
            slat_position = int(pattern.split('pos')[-1])
            apply_name_update('FLAT', 'h' + str(slat_side), 'position_' + str(slat_position), 'BLANK', '', plate, ind)

    export_standardized_plate_sheet(plate, output_folder, c_plate + '.xlsx')
print('FLAT STAPLE PLATES COMPLETE')

# CARGO HANDLE PREPARATION
output_folder = os.path.join(main_folder, 'cargo_plates')
create_dir_if_empty(output_folder)

for c_plate in [simpsons_mixplate_antihandles, simpsons_mixplate_antihandles_maxed, nelson_quimby_antihandles, seed_slat_purification_handles, paint_h5_handles, cnt_patterning, octahedron_patterning_v1]:
    sp_name = '_'.join(c_plate.split('_')[0:2])
    full_file = os.path.join(old_cargo_folder, c_plate + '.xlsx')
    print(sp_name)
    plate = read_dna_plate_mapping(full_file, data_type='2d_excel', plate_size=384).reset_index(drop=True)
    plate['concentration'] = concentration_library[sp_name]
    for ind, pattern in enumerate(plate['name'].tolist()):
        if '_' not in pattern:
            plate.at[ind, 'name'] = 'NON-SLAT OLIGO'
            plate.at[ind, 'description'] = pattern
            continue
        if '*' in pattern:
            plate.at[ind, 'name'] = 'NON-SLAT OLIGO'
            continue
        cargo = pattern.split('_')[0]
        if '-' in cargo:
            cargo = cargo.replace('-', '_')
        slat_position = ''.join(ch for ch in pattern.split('_')[-1] if ch.isdigit())
        orientation = pattern.split('_')[1]
        apply_name_update('CARGO', orientation, 'position_' + slat_position, cargo, '', plate, ind)

    export_standardized_plate_sheet(plate, output_folder, c_plate + '.xlsx')
print('CARGO HANDLE PLATES COMPLETE')
