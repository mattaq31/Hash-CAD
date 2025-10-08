import os

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates


########################################
# SETUP
design_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Crisscross Designs/CB015_3d_cube/'
echo_folder = os.path.join(design_folder, 'echo_run_oct_8', 'echo_commands')
lab_helper_folder = os.path.join(design_folder, 'echo_run_oct_8', 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

main_plates = get_cutting_edge_plates(100) # this is the first design that uses the new 100uM working stock concentrations

megastructure = Megastructure(import_design_file=os.path.join(design_folder, '3DCorner_V3_noauxiliaryslats.xlsx'))
megastructure.patch_placeholder_handles(main_plates)
megastructure.patch_flat_staples(main_plates[0]) # this plate contains only flat staples


########################################
# REPORTS
# megastructure.create_standard_graphical_report(os.path.join(design_folder, 'echo_run_oct_8'), generate_3d_video=True)
########################################
print('----')
# ECHO
single_handle_volume = 75 #nl

for s_key, slat in megastructure.slats.items():
    for position, handle in slat.H2_handles.items():
        if position == 16 or position == 17:
            handle['category'] = 'SKIP'

    for position, handle in slat.H5_handles.items():
        if position == 16 or position == 17:
            handle['category'] = 'SKIP'

print('Generating echo command sheets:')
echo_sheet = convert_slats_into_echo_commands(slat_dict=megastructure.slats,
                                              destination_plate_name='CB015_3DCorner',
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
                                              output_filename='CB015_3DCorner_echo_commands.csv')

prepare_all_standard_sheets(megastructure.slats, os.path.join(lab_helper_folder, 'CB015_3DCorner_lab_helper_sheets.xlsx'),
                            reference_single_handle_volume=single_handle_volume,
                            reference_single_handle_concentration=500,
                            echo_sheet=echo_sheet,  # previously generated via the echo command
                            handle_mix_ratio=15,
                            # setting to 15 as a buffer, technically only 10x handle:scaffold is required
                            peg_concentration=3,  # set to the concentration of PEG solution you have in stock
                            peg_groups_per_layer=2,
                            split_core_staple_pools=True)  # splits a layer into 4 different PEG groups)
