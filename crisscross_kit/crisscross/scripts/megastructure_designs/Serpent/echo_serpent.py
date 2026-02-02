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
experiment_folder = "C:/Users/Flori/Dropbox/CrissCross/Crisscross Designs/Katzi/Serpent"
echo_folder = os.path.join(experiment_folder, 'echo')
lab_helper_folder = os.path.join(experiment_folder, 'lab_helpers')
python_graphics_folder = os.path.join(experiment_folder, 'python_graphics')
create_dir_if_empty(echo_folder, lab_helper_folder, python_graphics_folder)

design_file = os.path.join(experiment_folder, 'Design', 'serpent_f.xlsx')

########## LOADING DESIGNS
megastructure = Megastructure(import_design_file=design_file)

regen_graphics = False
generate_echo = True

main_plates = get_cutting_edge_plates(handle_library_working_stock_concentration=200)
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)
src_007 = get_plateclass('HashCadPlate', simpsons_mixplate_antihandles, cargo_plate_folder)

valency_results = megastructure.get_parasitic_interactions()
print(f'Parasitic interactions - Max valency: {valency_results["worst_match_score"]}, effective valency: {valency_results["mean_log_score"]}')

if regen_graphics:
    megastructure.create_standard_graphical_report(python_graphics_folder, generate_3d_video=True)

megastructure.patch_placeholder_handles(main_plates + (src_004,))
megastructure.patch_placeholder_handles(main_plates)
megastructure.patch_flat_staples(main_plates[0]) # this plate contains only flat staples


# DBs and normal slats split into 2 different plates


all_slats = {}

all_slats_by_color = {}

for slat_id, slat in megastructure.slats.items():

    color = slat.unique_color

    # create new color bucket if needed
    if color not in all_slats_by_color:
        all_slats_by_color[color] = {}

    # store slat copy in correct color bucket
    all_slats_by_color[color][slat_id] = copy.copy(slat)

print("Found colors:")
for color, slats in all_slats_by_color.items():
    print(f"{color} : {len(slats)} slats")







tail_slat_colors= ['#42FD00','#FD0000','#053D00','#7D0101']

tail_slats = {}

for color in tail_slat_colors:

    # skip colors that do not exist in the structure
    if color not in all_slats_by_color:
        print(f"Warning: tail color {color} not found in megastructure")
        continue

    for slat_id, slat in all_slats_by_color[color].items():
        tail_slats[slat_id] = slat





fluorescent_head_colors = ['#FFB200', '#FF6B06', '#F8FF00']

fluo_head_slats = {}
normal_head_slats = {}

for slat_id, slat in megastructure.slats.items():

    if slat_id in tail_slats:
        continue

    slat_copy = copy.copy(slat)

    if slat.unique_color in fluorescent_head_colors:
        fluo_head_slats[slat_id] = slat_copy
    else:
        normal_head_slats[slat_id] = slat_copy


if generate_echo:

    commands_tailA = convert_slats_into_echo_commands(slat_dict=tail_slats,
                                                              destination_plate_name=f'tail_slats_A',
                                                              reference_transfer_volume_nl=150,
                                                              output_folder=echo_folder,
                                                              center_only_well_pattern=True,
                                                              plate_viz_type='barcode',
                                                              normalize_volumes=True,
                                                              output_filename=f'tail_slats_A.csv')



    prepare_all_standard_sheets(tail_slats, os.path.join(lab_helper_folder, f'tail_slats_A.xlsx'),
                                reference_single_handle_volume=150,
                                reference_single_handle_concentration=500,
                                echo_sheet=commands_tailA ,
                                handle_mix_ratio=15,
                                slat_mixture_volume=100,
                                peg_concentration=3,
                                split_core_staple_pools=True,
                                peg_groups_per_layer=2)

    commands_tailB = convert_slats_into_echo_commands(slat_dict=tail_slats,
                                                              destination_plate_name=f'tail_slats_B',
                                                              reference_transfer_volume_nl=150,
                                                              output_folder=echo_folder,
                                                              center_only_well_pattern=True,
                                                              plate_viz_type='barcode',
                                                              normalize_volumes=True,
                                                              output_filename=f'tail_slats_B.csv')



    prepare_all_standard_sheets(tail_slats, os.path.join(lab_helper_folder, f'tail_slats_B.xlsx'),
                                reference_single_handle_volume=150,
                                reference_single_handle_concentration=500,
                                echo_sheet=commands_tailB,
                                handle_mix_ratio=15,
                                slat_mixture_volume=100,
                                peg_concentration=3,
                                split_core_staple_pools=True,
                                peg_groups_per_layer=2)



    commands_fluo_head = convert_slats_into_echo_commands(slat_dict=fluo_head_slats,
                                                              destination_plate_name=f'fluo_head_slats',
                                                              reference_transfer_volume_nl=75,
                                                              output_folder=echo_folder,
                                                              center_only_well_pattern=True,
                                                              plate_viz_type='barcode',
                                                              normalize_volumes=True,
                                                              output_filename=f'fluo_head_slats.csv')

    prepare_all_standard_sheets(fluo_head_slats, os.path.join(lab_helper_folder, f'fluo_head_slats.xlsx'),
                                reference_single_handle_volume=75,
                                reference_single_handle_concentration=500,
                                echo_sheet=commands_fluo_head,
                                handle_mix_ratio=15,
                                slat_mixture_volume=50,
                                peg_concentration=3,
                                split_core_staple_pools=True,
                                peg_groups_per_layer=2)


    commands_normal_head = convert_slats_into_echo_commands(slat_dict=normal_head_slats,
                                                              destination_plate_name=f'normal_head_slats',
                                                              reference_transfer_volume_nl=75,
                                                              output_folder=echo_folder,
                                                              center_only_well_pattern=True,
                                                              plate_viz_type='barcode',
                                                              normalize_volumes=True,
                                                              output_filename=f'normal_head_slats.csv')

    prepare_all_standard_sheets(normal_head_slats, os.path.join(lab_helper_folder, f'normal_head_slats.xlsx'),
                                reference_single_handle_volume=75,
                                reference_single_handle_concentration=500,
                                echo_sheet=commands_normal_head,
                                handle_mix_ratio=15,
                                slat_mixture_volume=50,
                                peg_concentration=3,
                                split_core_staple_pools=True,
                                peg_groups_per_layer=2)

    # combine commands into one file

    commands_standard= pd.concat([commands_tailA, commands_tailB, commands_fluo_head, commands_normal_head])
    commands_standard.to_csv(os.path.join(echo_folder, "final_combined_commands.csv"), index=False)
