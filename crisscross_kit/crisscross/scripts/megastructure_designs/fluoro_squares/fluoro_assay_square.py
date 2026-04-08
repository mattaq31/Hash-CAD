import os
from collections import defaultdict

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates, get_plateclass
from crisscross.plate_mapping.plate_constants import seed_slat_purification_handles, cargo_plate_folder
from crisscross.helper_functions.simple_plate_visuals import visualize_plate_with_color_labels

########## CONFIG
experiment_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Crisscross Designs/Matthew/fluoro_assay_basic_square'
echo_folder = os.path.join(experiment_folder, 'echo')
lab_helper_folder = os.path.join(experiment_folder, 'lab_helpers')
create_dir_if_empty(echo_folder, lab_helper_folder)

design_file = os.path.join(experiment_folder, 'square_with_36_fluoros.xlsx')

########## LOADING DESIGNS
mega = Megastructure(import_design_file=design_file)

generate_echo = True
main_plates = get_cutting_edge_plates()
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)

mega.patch_placeholder_handles(main_plates + (src_004,))
mega.patch_flat_staples(main_plates[0])  # this plate contains only flat staples

valency_results = mega.get_parasitic_interactions()
print(f'Parasitic interactions for megastructure - Max valency: {valency_results["worst_match_score"]}, effective valency: {valency_results["mean_log_score"]}, similarity score: {valency_results["similarity_score"]}')

slat_fluoro_groups = defaultdict(set)
for slat_id, slat in mega.slats.items(): # removes handles from automated pipetting (since fluoro handles are still separately pipetted)
    for handle_id, handle in slat.H5_handles.items():
        if (slat_id, handle_id, 5) in mega.link_manager.handle_link_to_group:
            group_val = mega.link_manager.handle_link_to_group[(slat_id, handle_id, 5)]
            if group_val in mega.link_manager.handle_group_to_value:
                handle['category'] = 'SKIP'
            slat_fluoro_groups[handle_id].add(slat_id)

if generate_echo:
    ref_vol = 75
    echo_commands = convert_slats_into_echo_commands(slat_dict=mega.slats,
                                                        destination_plate_name=f'sq_36_fluoro',
                                                        reference_transfer_volume_nl=ref_vol,
                                                        output_folder=echo_folder,
                                                        center_only_well_pattern=True,
                                                        plate_viz_type='barcode',
                                                        normalize_volumes=True,
                                                        output_filename=f'sq_36_fluoro_echo.csv')

    prepare_all_standard_sheets(mega.slats, os.path.join(lab_helper_folder, f'sq_36_fluoro.xlsx'),
                                reference_single_handle_volume=ref_vol,
                                reference_single_handle_concentration=500,
                                echo_sheet=echo_commands,
                                handle_mix_ratio=15,
                                slat_mixture_volume=50,
                                peg_concentration=3,
                                split_core_staple_pools=True,
                                peg_groups_per_layer=2)

    master_mix_color_dict = defaultdict(list)

    group_color_dict = {9: 'red', 23: 'blue', 30: 'green'}
    color_description_dict = {'red': 'Slat Pos 9, H34',
                              'blue': 'Slat Pos 23, H40',
                              'green': 'Slat Pos 30, H58'}

    for group, slat_ids in slat_fluoro_groups.items():
        for s in slat_ids:
            echo_index = echo_commands[echo_commands['Component'].str.contains(fr"{s}_h\d_", na=False)].index[0]
            plate_well = echo_commands.loc[echo_index]['Destination Well']
            master_mix_color_dict[plate_well].append(group_color_dict[group])

    visualize_plate_with_color_labels('96', master_mix_color_dict,
                                      color_label_dict=color_description_dict,
                                      plate_title=f'Fluoro Handle Replacement Map (200nl each)',
                                      save_folder=lab_helper_folder,
                                      save_file='fluoro_master_map',
                                      direct_show=True)
