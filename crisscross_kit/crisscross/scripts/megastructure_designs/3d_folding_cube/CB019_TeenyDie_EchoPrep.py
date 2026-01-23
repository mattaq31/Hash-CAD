import os

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates, simpsons_mixplate_antihandles, get_plateclass, cargo_plate_folder


# SETUP

design_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Crisscross Designs/CB019_TeenyDie'
echo_folder = os.path.join(design_folder, 'echo_run_jan_22', 'echo')
lab_helper_folder = os.path.join(design_folder, 'echo_run_jan_22', 'lab_helpers')
create_dir_if_empty(echo_folder, lab_helper_folder)

main_plates = get_cutting_edge_plates(200)
src_007 = get_plateclass('HashCadPlate', simpsons_mixplate_antihandles, cargo_plate_folder)

megastructure = Megastructure(import_design_file=os.path.join(design_folder, 'TeenyDie_V9_slats_flipped.xlsx'))
megastructure.patch_placeholder_handles(main_plates + (src_007,))
megastructure.patch_flat_staples(main_plates[0])  # this plate contains only flat staples

valency_results = megastructure.get_parasitic_interactions()
print(f'Parasitic interactions - Max valency: {valency_results["worst_match_score"]}, effective valency: {valency_results["mean_log_score"]}')

########################################
# REPORTS
# megastructure.create_standard_graphical_report(os.path.join(design_folder, 'echo_run_oct_8'), generate_3d_video=True)
########################################
print('----')
# ECHO
single_handle_volume = 75 #nl

# WANT TO SKIP POSITIONS 16 AND 17 FOR ALL SLATS EXCEPT THOSE WITHIN "SPECIAL," WHERE I WOULD LIKE TO SKIP 15 AND 16 INSTEAD

special = {'layer2-slat2','layer2-slat3','layer2-slat4','layer2-slat5','layer2-slat6',
           'layer2-slat7','layer2-slat8','layer2-slat9','layer2-slat10','layer2-slat11',
           'layer2-slat12','layer2-slat13','layer2-slat14','layer2-slat15',
           'layer2-slat54','layer2-slat55'}

for s_key, slat in megastructure.slats.items():
    pos_to_skip = {15, 16} if s_key in special else {16, 17}

    for pos in pos_to_skip:
        if pos in slat.H2_handles:
            slat.H2_handles[pos]['category'] = 'SKIP'
        if pos in slat.H5_handles:
            slat.H5_handles[pos]['category'] = 'SKIP'

print('Generating echo command sheets:')
echo_sheet = convert_slats_into_echo_commands(slat_dict=megastructure.slats,
                                              destination_plate_name='CB019_TeenyDie',
                                              reference_transfer_volume_nl=single_handle_volume,
                                              # base liquid transfer volume for one staple at the reference concentration
                                              reference_concentration_uM=500,
                                              # reference concentration for one staple
                                              output_folder=echo_folder,
                                              center_only_well_pattern=True,
                                              # set to true to only use the center wells of the output plate
                                              plate_viz_type='barcode',
                                              normalize_volumes=True,
                                              # set to true to normalize the volumes of each output well (by adding extra buffer or water to wells that have low volumes)
                                              output_filename='CB019_TeenyDie_echo_commands.csv')

prepare_all_standard_sheets(megastructure.slats, os.path.join(lab_helper_folder, 'CB019_TeenyDie_lab_helper_sheets.xlsx'),
                            reference_single_handle_volume=single_handle_volume,
                            reference_single_handle_concentration=500,
                            echo_sheet=echo_sheet,  # previously generated via the echo command
                            handle_mix_ratio=15,
                            # setting to 15 as a buffer, technically only 10x handle:scaffold is required
                            peg_concentration=3,  # set to the concentration of PEG solution you have in stock
                            peg_groups_per_layer=2,
                            split_core_staple_pools=True)  # splits a layer into 4 different PEG groups)
