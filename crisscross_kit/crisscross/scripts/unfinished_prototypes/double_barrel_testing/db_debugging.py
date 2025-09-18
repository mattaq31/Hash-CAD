import os
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
import copy

########## CONFIG
# update these depending on user
experiment_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/hash_cad_validation_designs/double_barrels'
echo_folder = os.path.join(experiment_folder, 'echo_commands')
lab_helper_folder = os.path.join(experiment_folder, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

base_design_import_files = [os.path.join(experiment_folder, 'designs', 'Tiny Hexagon Optim.xlsx')]

generate_echo = True
generate_lab_helpers = True

########## LOADING AND CHECKING DESIGN
for design_file in base_design_import_files:
    design_name = os.path.split(design_file)[1].split('.')[0]
    print('%%%%%%%%%%%%%%%')
    print('Processing design: %s' % design_name)
    megastructure = Megastructure(import_design_file=design_file)

    if design_name == 'Tiny Hexagon Optim':
        db_slats = {}
        # cannot add double-barrel slats for seeded area as we don't have the seed handles for positions 28-32
        # for s_id in range(1, 16, 2):
        #     db_slats[f'layer1-slat{s_id}'] = {'H5':[[f'layer1-slat{s_id}', list(range(1, 17))], [f'layer1-slat{s_id+1}', list(range(16, 0, -1))]]}
        for s_id in range(17, 32, 2):
            db_slats[f'layer1-slat{s_id}'] = {'H5':[[f'layer1-slat{s_id}', list(range(1, 17))], [f'layer1-slat{s_id+1}', list(range(16, 0, -1))]], 'H2': []}
        for s_id in range(33, 48, 2):
            db_slats[f'layer1-slat{s_id}'] = {'H5':[[f'layer1-slat{s_id}', list(range(1, 17))], [f'layer1-slat{s_id+1}', list(range(16, 0, -1))]], 'H2': []}

        for s_id in range(1, 16, 2):
            db_slats[f'layer2-slat{s_id}'] = {'H2':[[f'layer2-slat{s_id}', list(range(1, 17))], [f'layer2-slat{s_id+1}', list(range(16, 0, -1))]], 'H5': []}
        for s_id in range(17, 32, 2):
            db_slats[f'layer2-slat{s_id}'] = {'H2':[[f'layer2-slat{s_id}', list(range(1, 17))], [f'layer2-slat{s_id+1}', list(range(16, 0, -1))]], 'H5': []}
        for s_id in range(33, 48, 2):
            db_slats[f'layer2-slat{s_id}'] = {'H2':[[f'layer2-slat{s_id}', list(range(1, 17))], [f'layer2-slat{s_id+1}', list(range(16, 0, -1))]], 'H5': []}


    for main_id, handle_edits in db_slats.items():
        slats_to_delete = set()
        new_slat_name = 'D-' + main_id
        new_slat = copy.deepcopy(megastructure.slats[main_id])
        new_slat.ID = new_slat_name
        new_slat.slat_position_to_coordinate = {}
        new_slat.slat_coordinate_to_position = {}
        for side, handle_sequence in handle_edits.items():
            handle_pos = 1
            for (s_id, handle_list) in handle_sequence:
                for consecutive_position, handle_extraction_id in enumerate(handle_list):
                    slats_to_delete.add(s_id)
                    if side == 'H2':
                        new_slat.H2_handles[handle_pos] = megastructure.slats[s_id].H2_handles[handle_extraction_id]
                    else:
                        new_slat.H5_handles[handle_pos] = megastructure.slats[s_id].H5_handles[handle_extraction_id]

                    placeholder_name = f'handle|{handle_pos}|h{side[-1]}'
                    if placeholder_name not in new_slat.placeholder_list:
                        new_slat.placeholder_list.append(placeholder_name)

                    new_slat.slat_position_to_coordinate[handle_pos] = megastructure.slats[s_id].slat_position_to_coordinate[handle_extraction_id]
                    coord_to_move = megastructure.slats[s_id].slat_position_to_coordinate[handle_extraction_id]
                    new_slat.slat_coordinate_to_position[coord_to_move] = handle_pos

                    handle_pos += 1

        megastructure.slats[new_slat_name] = new_slat
        for s_id in slats_to_delete:
            del(megastructure.slats[s_id])

    megastructure.create_standard_graphical_report(os.path.join('/Users/matt/Desktop', f'{design_name}_graphics'), filename_prepend=f'{design_name}_', generate_3d_video=True)
    # megastructure.export_design(f'{design_name}.xlsx', '/Users/matt/Desktop')
