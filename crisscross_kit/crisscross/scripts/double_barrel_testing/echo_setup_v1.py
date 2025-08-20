import os
import copy

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates

########## CONFIG
# update these depending on user
experiment_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/hash_cad_validation_designs/double_barrels'
echo_folder = os.path.join(experiment_folder, 'echo_commands')
lab_helper_folder = os.path.join(experiment_folder, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

base_design_import_files = [os.path.join(experiment_folder,'designs', 'Double Barrel Wario Optim.xlsx'),
                            os.path.join(experiment_folder, 'designs', 'DoubleBarrel_L Optim.xlsx'),
                            os.path.join(experiment_folder, 'designs', 'Tiny Hexagon Optim.xlsx')]

generate_echo = True
generate_lab_helpers = True

main_plates = get_cutting_edge_plates(100)


########## LOADING AND CHECKING DESIGN
for design_file in base_design_import_files:
    design_name = os.path.split(design_file)[1].split('.')[0]

    print('%%%%%%%%%%%%%%%')
    print('Processing design: %s' % design_name)
    megastructure = Megastructure(import_design_file=design_file)
    hamming_results = multirule_oneshot_hamming(megastructure.generate_slat_occupancy_grid(), megastructure.generate_assembly_handle_grid(), request_substitute_risk_score=True)
    print('Hamming distance from imported array: %s, Duplication Risk: %s' % (hamming_results['Universal'], hamming_results['Substitute Risk']))

    ########## PATCHING PLATES

    if design_name == 'Double Barrel Wario Optim':
        db_slats = {}
        for s_id in range(33, 48, 2):
            db_slats[f'layer2-slat{s_id}'] = {'H2':[[f'layer2-slat{s_id}', list(range(17, 33))], [f'layer2-slat{s_id+1}', list(range(32, 16, -1))]], 'H5': []}
        for s_id in range(17, 32, 2):
            db_slats[f'layer1-slat{s_id}'] = {'H5':[[f'layer1-slat{s_id}', list(range(1, 17))], [f'layer1-slat{s_id+1}', list(range(16, 0, -1))]], 'H2': []}

    elif design_name == 'DoubleBarrel_L Optim':
        db_slats = {}
        for s_id in range(17, 48, 2):
            db_slats[f'layer1-slat{s_id}'] = {'H5':[[f'layer1-slat{s_id}', list(range(1, 17))], [f'layer1-slat{s_id+1}', list(range(16, 0, -1))]], 'H2': []}

        for s_id in range(1, 32, 2):
            db_slats[f'layer2-slat{s_id}'] = {'H5':[[f'layer2-slat{s_id}', list(range(1, 17))], [f'layer2-slat{s_id+1}', list(range(16, 0, -1))]],
                                              'H2': [[f'layer2-slat{s_id}', list(range(1, 17))], [f'layer2-slat{s_id+1}', list(range(16, 0, -1))]]}

        for s_id in range(1, 16, 2):
            db_slats[f'layer3-slat{s_id}'] = {'H2':[[f'layer3-slat{s_id}', list(range(17, 33))], [f'layer3-slat{s_id+1}', list(range(32, 16, -1))]], 'H5': []}
        for s_id in range(33, 48, 2):
            db_slats[f'layer3-slat{s_id}'] = {'H2':[[f'layer3-slat{s_id}', list(range(1, 17))], [f'layer3-slat{s_id+1}', list(range(16, 0, -1))]], 'H5': []}

    elif design_name == 'Tiny Hexagon Optim':
        db_slats = {}
        for s_id in range(1, 16, 2):
            db_slats[f'layer1-slat{s_id}'] = {'H5':[[f'layer1-slat{s_id}', list(range(1, 17))], [f'layer1-slat{s_id+1}', list(range(16, 0, -1))]], 'H2': []}
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
        for side, handle_sequence in handle_edits.items():
            handle_pos = 1
            for (s_id, handle_list) in handle_sequence:
                for handle_extraction_id in handle_list:
                    slats_to_delete.add(s_id)
                    if side == 'H2':
                        new_slat.H2_handles[handle_pos] = megastructure.slats[s_id].H2_handles[handle_extraction_id]
                    else:
                        new_slat.H5_handles[handle_pos] = megastructure.slats[s_id].H5_handles[handle_extraction_id]
                    placeholder_name = f'handle|{handle_pos}|h{side[-1]}'
                    if placeholder_name not in new_slat.placeholder_list:
                        new_slat.placeholder_list.append(placeholder_name)

                    handle_pos += 1

        megastructure.slats[new_slat_name] = new_slat
        for s_id in slats_to_delete:
            del(megastructure.slats[s_id])

    megastructure.patch_placeholder_handles(main_plates)
    megastructure.patch_flat_staples(main_plates[0])

    for s_id, slat in megastructure.slats.items():
        if 'D-' in s_id:
            slat.H2_handles[16]['category'] = 'SKIP'
            slat.H5_handles[16]['category'] = 'SKIP'
            del(slat.H2_handles[16]['descriptor'])
            del(slat.H5_handles[16]['descriptor'])

    target_volume = 75 # nl per staple
    if generate_echo:
        echo_sheet_1 = convert_slats_into_echo_commands(slat_dict=megastructure.slats,
                                                        destination_plate_name=f'{design_name}',
                                                        reference_transfer_volume_nl=target_volume,
                                                        output_folder=echo_folder,
                                                        center_only_well_pattern=True,
                                                        plate_viz_type='barcode',
                                                        normalize_volumes= True,
                                                        output_filename=f'{design_name}_echo_commands.csv')

    if generate_lab_helpers:
        prepare_all_standard_sheets(megastructure.slats, os.path.join(lab_helper_folder, f'{design_name}_experiment_helpers.xlsx'),
                                    reference_single_handle_volume=target_volume,
                                    reference_single_handle_concentration=500,
                                    echo_sheet=None if not generate_echo else echo_sheet_1,
                                    handle_mix_ratio=15,
                                    slat_mixture_volume=50,
                                    peg_concentration=3,
                                    split_core_staple_pools=True,
                                    peg_groups_per_layer=4)
