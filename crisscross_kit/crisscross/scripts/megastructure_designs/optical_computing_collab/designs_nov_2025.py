import os
import pandas as pd
import copy
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates, get_plateclass
from crisscross.plate_mapping.plate_constants import seed_slat_purification_handles, cargo_plate_folder, simpsons_mixplate_antihandles_maxed


########## CONFIG
# update these depending on user
experiment_folder = '/Users/yichenzhao/Documents/Wyss/Projects/Columbia/New Mat Designs Nov 2025'
experiment_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Crisscross Designs/New Mat Designs Nov 2025'
echo_folder = os.path.join(experiment_folder, 'echo')
lab_helper_folder = os.path.join(experiment_folder, 'lab_helpers')
python_graphics_folder = os.path.join(experiment_folder, 'python_graphics')
create_dir_if_empty(echo_folder, lab_helper_folder, python_graphics_folder)

ThreeEdnaSquare_design = os.path.join(experiment_folder, 'allantiEdna_3site_mod 1.xlsx')
FourEdnaSquare_design = os.path.join(experiment_folder, 'allantiEdna_4site_mod1.xlsx')
ThreeEdnaHex_design = os.path.join(experiment_folder, 'hexstar_antiEdna_3site_mod2.xlsx')
FourEdnaHex_design = os.path.join(experiment_folder, 'hexstar_antiEdna_4site_mod1.xlsx')

########## LOADING DESIGNS
s3 = Megastructure(import_design_file=ThreeEdnaSquare_design)
s4 = Megastructure(import_design_file=FourEdnaSquare_design)
h3 = Megastructure(import_design_file=ThreeEdnaHex_design)
h4 = Megastructure(import_design_file=FourEdnaHex_design)


regen_graphics = False
generate_echo = True

main_plates = get_cutting_edge_plates(200)
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)
src_010 = get_plateclass('HashCadPlate', simpsons_mixplate_antihandles_maxed, cargo_plate_folder)

valency_results1 = s3.get_parasitic_interactions()
print(f'3EdnaSquare - Max valency: {valency_results1["worst_match_score"]}, effective valency: {valency_results1["mean_log_score"]}')
valency_results2 = s4.get_parasitic_interactions()
print(f'4EdnaSquare - Max valency: {valency_results2["worst_match_score"]}, effective valency: {valency_results2["mean_log_score"]}')
valency_results3 = h3.get_parasitic_interactions()
print(f'3EdnaHex - Max valency: {valency_results3["worst_match_score"]}, effective valency: {valency_results3["mean_log_score"]}')
valency_results4 = h4.get_parasitic_interactions()
print(f'4EdnaHex - Max valency: {valency_results4["worst_match_score"]}, effective valency: {valency_results4["mean_log_score"]}')

s3.patch_placeholder_handles(main_plates + (src_004,)+(src_010,))
s4.patch_placeholder_handles(main_plates + (src_004,)+(src_010,))
h3.patch_placeholder_handles(main_plates + (src_004,)+(src_010,))
h4.patch_placeholder_handles(main_plates + (src_004,)+(src_010,))

s3.patch_flat_staples(main_plates[0])
s4.patch_flat_staples(main_plates[0])
h3.patch_flat_staples(main_plates[0])
h4.patch_flat_staples(main_plates[0])


if regen_graphics:
    s3.create_standard_graphical_report(python_graphics_folder, filename_prepend='square_three_pos_', generate_3d_video=True)
    s4.create_standard_graphical_report(python_graphics_folder, filename_prepend='square_four_pos_', generate_3d_video=True)
    h3.create_standard_graphical_report(python_graphics_folder, filename_prepend='star_three_pos_', generate_3d_video=True)
    h4.create_standard_graphical_report(python_graphics_folder, filename_prepend='star_four_pos_', generate_3d_video=True)

if generate_echo:
    target_volume = 75 # nl per staple

    # square sheets and commands
    # split into two - bottom slats and top slats.  The bottom slats will be done once with double volume.

    # select only slats in bottom layer
    selected_slats = {}
    for s_name, s in s3.slats.items():
        if s.layer != 2:
            selected_slats[s_name] = copy.deepcopy(s)

    # select all slats in top layer from both designs
    selected_upper_slats = {}
    for s_name, s in s3.slats.items():
        if s.layer == 2:
            selected_upper_slats[s_name + '-3'] = copy.deepcopy(s)
            selected_upper_slats[s_name + '-3'].ID = s_name + '-3'

    for s_name, s in s4.slats.items():
        if s.layer == 2:
            selected_upper_slats[s_name + '-4'] = copy.deepcopy(s)
            selected_upper_slats[s_name + '-4'].ID = s_name + '-4'
            selected_upper_slats[s_name + '-4'].unique_color = '#0040B8FF' # blue


    echo_sheet_1 = convert_slats_into_echo_commands(slat_dict=selected_slats,
                                                    destination_plate_name=f'square_bottoms',
                                                    reference_transfer_volume_nl=target_volume * 2,
                                                    output_folder=echo_folder,
                                                    center_only_well_pattern=True,
                                                    plate_viz_type='barcode',
                                                    normalize_volumes=True,
                                                    output_filename=f'square_bottom_echo.csv')

    echo_sheet_2 = convert_slats_into_echo_commands(slat_dict=selected_upper_slats,
                                                    destination_plate_name=f'square_tops',
                                                    reference_transfer_volume_nl=target_volume,
                                                    output_folder=echo_folder,
                                                    center_only_well_pattern=True,
                                                    plate_viz_type='barcode',
                                                    normalize_volumes=True,
                                                    output_filename=f'square_top_echo.csv')

    prepare_all_standard_sheets(selected_slats, os.path.join(lab_helper_folder, f'square_bottom_helpers.xlsx'),
                                reference_single_handle_volume=target_volume * 2,
                                reference_single_handle_concentration=500,
                                echo_sheet=echo_sheet_1,
                                handle_mix_ratio=15,
                                slat_mixture_volume=100,
                                peg_concentration=3,
                                split_core_staple_pools=True,
                                peg_groups_per_layer=2)

    prepare_all_standard_sheets(selected_upper_slats, os.path.join(lab_helper_folder, f'square_top_helpers.xlsx'),
                                reference_single_handle_volume=target_volume,
                                reference_single_handle_concentration=500,
                                echo_sheet=echo_sheet_2,
                                handle_mix_ratio=15,
                                slat_mixture_volume=50,
                                peg_concentration=3,
                                split_core_staple_pools=True,
                                peg_groups_per_layer=4)

    # hexstar sheets and commands

    # select only slats in layers 1 and 2
    selected_slats = {}
    for s_name, s in h3.slats.items():
        if s.layer != 3:
            selected_slats[s_name] = copy.deepcopy(s)

    # only lower layer slats here
    echo_sheet_3 = convert_slats_into_echo_commands(slat_dict=selected_slats,
                                                    destination_plate_name=f'hexstar_lower',
                                                    reference_transfer_volume_nl=target_volume,
                                                    output_folder=echo_folder,
                                                    center_only_well_pattern=True,
                                                    plate_viz_type='barcode',
                                                    normalize_volumes=True,
                                                    output_filename=f'hexstar_lower_echo.csv')

    prepare_all_standard_sheets(selected_slats, os.path.join(lab_helper_folder, f'hexstar_lower_helpers.xlsx'),
                                reference_single_handle_volume=target_volume,
                                reference_single_handle_concentration=500,
                                echo_sheet=echo_sheet_3,
                                handle_mix_ratio=15,
                                slat_mixture_volume=50,
                                peg_concentration=3,
                                split_core_staple_pools=True,
                                peg_groups_per_layer=2)

    # do upper layer slats for both designs together

    selected_upper_slats = {}
    for s_name, s in h3.slats.items():
        if s.layer == 3:
            selected_upper_slats[s_name + '-3'] = copy.deepcopy(s)
            selected_upper_slats[s_name + '-3'].ID = s_name + '-3'

    for s_name, s in h4.slats.items():
        if s.layer == 3:
            selected_upper_slats[s_name + '-4'] = copy.deepcopy(s)
            selected_upper_slats[s_name + '-4'].ID = s_name + '-4'
            selected_upper_slats[s_name + '-4'].unique_color = '#0040B8FF' # blue

    echo_sheet_4 = convert_slats_into_echo_commands(slat_dict=selected_upper_slats,
                                                    destination_plate_name=f'hexstar_upper',
                                                    reference_transfer_volume_nl=target_volume,
                                                    output_folder=echo_folder,
                                                    center_only_well_pattern=True,
                                                    plate_viz_type='barcode',
                                                    normalize_volumes=True,
                                                    output_filename=f'hexstar_upper_echo.csv')

    prepare_all_standard_sheets(selected_upper_slats, os.path.join(lab_helper_folder, f'hexstar_upper_helpers.xlsx'),
                                reference_single_handle_volume=target_volume,
                                reference_single_handle_concentration=500,
                                echo_sheet=echo_sheet_4,
                                handle_mix_ratio=15,
                                slat_mixture_volume=50,
                                peg_concentration=3,
                                split_core_staple_pools=True,
                                peg_groups_per_layer=4)

design_files_to_combine = [os.path.join(echo_folder, 'square_bottom_echo.csv'),
                           os.path.join(echo_folder, 'square_top_echo.csv'),
                           os.path.join(echo_folder, 'hexstar_lower_echo.csv'),
                           os.path.join(echo_folder, 'hexstar_upper_echo.csv')]

# read in each csv file, combine together and then save to a new output file
combined_csv = pd.concat([pd.read_csv(f) for f in design_files_to_combine])

combined_csv.to_csv(os.path.join(echo_folder, "allecho.csv"), index=False)
