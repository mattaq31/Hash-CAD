import os
import pandas as pd
import copy

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty, plate96
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates, get_plateclass
from crisscross.plate_mapping.plate_constants import seed_slat_purification_handles, cargo_plate_folder

########## CONFIG
# update these depending on user
experiment_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Crisscross Designs/MAD DB Ribbon'
echo_folder = os.path.join(experiment_folder, 'echo')
lab_helper_folder = os.path.join(experiment_folder, 'lab_helpers')
python_graphics_folder = os.path.join(experiment_folder, 'python_graphics')
create_dir_if_empty(echo_folder, lab_helper_folder, python_graphics_folder)

design_file = os.path.join(experiment_folder, 'design', 'design_evolved_handles_linked.xlsx')

########## LOADING DESIGNS
megastructure = Megastructure(import_design_file=design_file)

regen_graphics = False
generate_echo = True

main_plates = get_cutting_edge_plates(200) # this is the first design that uses the new 100uM working stock concentrations
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)

valency_results = megastructure.get_parasitic_interactions()
print(f'Parasitic interactions - Max valency: {valency_results["worst_match_score"]}, effective valency: {valency_results["mean_log_score"]}')

if regen_graphics:
    megastructure.create_standard_graphical_report(python_graphics_folder, generate_3d_video=True)

megastructure.patch_placeholder_handles(main_plates + (src_004,))
megastructure.patch_flat_staples(main_plates[0]) # this plate contains only flat staples

for s_id, slat in megastructure.slats.items():
    if slat.slat_type == 'DB-L':
        slat.H2_handles[16]['category'] = 'SKIP'
        slat.H5_handles[16]['category'] = 'SKIP'


# repeating units will be prepared with a higher volume

# group 1 - 3*
# group 2 - 1*
slat_group_1 = {}
slat_group_2 = {}

group_2_slat_dict = {2:list(range(33, 49)), 1:list(range(1, 17)) + list(range(17, 25))}
group_2_slats = []

for layer, slat_id in group_2_slat_dict.items():
    for slat_numeral in slat_id:
        group_2_slats.append(f'layer{layer}-slat{slat_numeral}')

for slat_id, slat in megastructure.slats.items():
    if slat_id in group_2_slats:
        slat_group_2[slat_id] = copy.copy(slat)
    else:
        slat_group_1[slat_id] = copy.copy(slat)


if generate_echo:
    # splitting different slat volumes (I guess I could have combined them together, but whatever)
    # first create plate viz for all slats
    commands_all_positions = convert_slats_into_echo_commands(slat_dict=megastructure.slats,
                                                              destination_plate_name=f'ignore',
                                                              reference_transfer_volume_nl=75,
                                                              output_folder=echo_folder,
                                                              center_only_well_pattern=False,
                                                              plate_viz_type='barcode',
                                                              normalize_volumes=False,
                                                              output_filename=f'full_plate.csv')

    # next create echo commands in two files separately
    group_1_positioning = {}
    group_2_positioning = {}
    for index, (slat_id, slat) in enumerate(megastructure.slats.items()):
        if slat_id in group_2_slats:
            group_2_positioning[slat_id] = (1, plate96[index])
        else:
            group_1_positioning[slat_id] = (1, plate96[index])

    one_time_echo_commands = convert_slats_into_echo_commands(slat_dict=slat_group_2,
                                                              destination_plate_name=f'double_barrel_ribbon',
                                                              reference_transfer_volume_nl=75,
                                                              output_folder=echo_folder,
                                                              center_only_well_pattern=False,
                                                              plate_viz_type='barcode',
                                                              normalize_volumes=True,
                                                              manual_plate_well_assignments=group_2_positioning,
                                                              output_filename=f'one_time_slats.csv')

    # Repeating unit slats will have special handles for fluorescent labelling (handle 58 pos 30 and 2)
    # These need to be handled manually
    for slat_id, slat in slat_group_1.items():
        for handle_id, handle in slat.H5_handles.items():
            if handle_id == 30 or handle_id == 2:
                if handle['value'] == '58':
                    del handle['plate']

    repeating_unit_echo_commands = convert_slats_into_echo_commands(slat_dict=slat_group_1,
                                                                    destination_plate_name=f'double_barrel_ribbon',
                                                                    reference_transfer_volume_nl=225,
                                                                    output_folder=echo_folder,
                                                                    output_empty_wells=True,
                                                                    center_only_well_pattern=False,
                                                                    plate_viz_type='barcode',
                                                                    normalize_volumes=True,
                                                                    manual_plate_well_assignments=group_1_positioning,
                                                                    output_filename=f'repeat_unit_slats.csv')

    prepare_all_standard_sheets(slat_group_2, os.path.join(lab_helper_folder, f'one_time_slats_helpers.xlsx'),
                                reference_single_handle_volume=75,
                                reference_single_handle_concentration=500,
                                echo_sheet=one_time_echo_commands,
                                handle_mix_ratio=15,
                                slat_mixture_volume=50,
                                peg_concentration=3,
                                split_core_staple_pools=True,
                                peg_groups_per_layer=2)

    prepare_all_standard_sheets(slat_group_1, os.path.join(lab_helper_folder, f'repeat_unit_helpers.xlsx'),
                                reference_single_handle_volume=225,
                                reference_single_handle_concentration=500,
                                echo_sheet=repeating_unit_echo_commands,
                                handle_mix_ratio=15,
                                slat_mixture_volume=150,
                                peg_concentration=3,
                                split_core_staple_pools=True,
                                peg_groups_per_layer=2)

    # combine commands into one file
    combined_csv = pd.concat([one_time_echo_commands, repeating_unit_echo_commands])
    combined_csv.to_csv(os.path.join(echo_folder, "final_combined_commands.csv"), index=False)
