import os
import pandas as pd
import copy

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty, plate96
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates, get_plateclass
from crisscross.plate_mapping.plate_constants import seed_slat_purification_handles, cargo_plate_folder, simpsons_mixplate_antihandles

########## CONFIG
# update these depending on user
experiment_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Papers/double_barrels/design_library/heart'
echo_folder = os.path.join(experiment_folder, 'echo')
lab_helper_folder = os.path.join(experiment_folder, 'lab_helpers')
python_graphics_folder = os.path.join(experiment_folder, 'python_graphics')
create_dir_if_empty(echo_folder, lab_helper_folder, python_graphics_folder)

design_file = os.path.join(experiment_folder, 'designs', 'heart.xlsx')

########## LOADING DESIGNS
megastructure = Megastructure(import_design_file=design_file)

regen_graphics = False
generate_echo = True

main_plates = get_cutting_edge_plates(200)
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)
src_007 = get_plateclass('HashCadPlate', simpsons_mixplate_antihandles, cargo_plate_folder)

valency_results = megastructure.get_parasitic_interactions()
print(f'Parasitic interactions - Max valency: {valency_results["worst_match_score"]}, effective valency: {valency_results["mean_log_score"]}')

if regen_graphics:
    megastructure.create_standard_graphical_report(python_graphics_folder, generate_3d_video=True)

megastructure.patch_placeholder_handles(main_plates + (src_004, src_007))
megastructure.patch_flat_staples(main_plates[0]) # this plate contains only flat staples

del megastructure.slats['layer6-slat1']
del megastructure.slats['layer1-slat1']

for s_id, slat in megastructure.slats.items():
    if slat.slat_type == 'DB-L':
        slat.H2_handles[16]['category'] = 'SKIP'
        slat.H5_handles[16]['category'] = 'SKIP'

# DBs and normal slats split into 2 different plates

# group 1 - 3*
# group 2 - 1*
slat_group_1 = {}
slat_group_2 = {}

for slat_id, slat in megastructure.slats.items():
    if slat.slat_type == 'DB-L':
        slat_group_2[slat_id] = copy.copy(slat)
    else:
        slat_group_1[slat_id] = copy.copy(slat)

if generate_echo:

    commands_standard = convert_slats_into_echo_commands(slat_dict=slat_group_1,
                                                              destination_plate_name=f'heart_standard_slats',
                                                              reference_transfer_volume_nl=75,
                                                              output_folder=echo_folder,
                                                              center_only_well_pattern=True,
                                                              plate_viz_type='barcode',
                                                              normalize_volumes=True,
                                                              output_filename=f'heart_standard_slats_echo.csv')

    commands_barrels = convert_slats_into_echo_commands(slat_dict=slat_group_2,
                                                              destination_plate_name=f'heart_double_barrels',
                                                              reference_transfer_volume_nl=75,
                                                              output_folder=echo_folder,
                                                              center_only_well_pattern=True,
                                                              plate_viz_type='barcode',
                                                              normalize_volumes=True,
                                                              output_filename=f'heart_double_barrels_echo.csv')

    prepare_all_standard_sheets(slat_group_1, os.path.join(lab_helper_folder, f'heart_standard_slats_helpers.xlsx'),
                                reference_single_handle_volume=75,
                                reference_single_handle_concentration=500,
                                echo_sheet=commands_standard,
                                handle_mix_ratio=15,
                                slat_mixture_volume=50,
                                peg_concentration=3,
                                split_core_staple_pools=True,
                                peg_groups_per_layer=2)

    prepare_all_standard_sheets(slat_group_2, os.path.join(lab_helper_folder, f'heart_double_barrels_helpers.xlsx'),
                                reference_single_handle_volume=75,
                                reference_single_handle_concentration=500,
                                echo_sheet=commands_barrels,
                                handle_mix_ratio=15,
                                slat_mixture_volume=50,
                                peg_concentration=3,
                                split_core_staple_pools=True,
                                peg_groups_per_layer=2)

    # combine commands into one file
    combined_csv = pd.concat([commands_standard, commands_barrels])
    combined_csv.to_csv(os.path.join(echo_folder, "final_combined_commands.csv"), index=False)
