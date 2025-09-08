import numpy as np
import os
import pandas as pd

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming
from crisscross.core_functions.slats import Slat
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.helper_functions import create_dir_if_empty
from crisscross.plate_mapping import get_cutting_edge_plates, get_cargo_plates

########## CONFIG

user_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Crisscross Designs/'
# user_folder = '/Users/yichenzhao/Documents/Wyss/Projects/Columbia/'
design_folder = os.path.join(user_folder, 'YXZ006_Nelson_Quimby_Mats')

NQ_import_file = os.path.join(design_folder, 'colsquareNQ.xlsx')
allE_import_file = os.path.join(design_folder, 'allantiEdna.xlsx')

echo_folder = os.path.join(design_folder, 'echo_commands')
lab_helper_folder = os.path.join(design_folder, 'lab helpers')

create_dir_if_empty(echo_folder, lab_helper_folder)
generate_echo=True
regen_graphics = False
export_design = False
generate_lab_helpers = True

######### Import
NQ_mega = Megastructure(import_design_file=NQ_import_file)
allE_mega = Megastructure(import_design_file=allE_import_file)

hamming_NQ = multirule_oneshot_hamming(NQ_mega.generate_slat_occupancy_grid(), NQ_mega.generate_assembly_handle_grid(),
                                                      request_substitute_risk_score=True)
hamming_allE = multirule_oneshot_hamming(allE_mega.generate_slat_occupancy_grid(), allE_mega.generate_assembly_handle_grid(),
                                                      request_substitute_risk_score=True)

print('Hamming distance from optimized array: %s %s, Duplication Risk: %s %s' % (hamming_NQ['Universal'],hamming_allE['Universal'],hamming_NQ['Substitute Risk'],hamming_allE['Substitute Risk']))

#PATCHING PLATES
#core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, all_8064_seed_plugs = get_cutting_edge_plates()
cargo_plates = get_cargo_plates()
plates= get_cutting_edge_plates(100)

########## ADDING TOEHOLD CARGO
doublepure_key = {1 : "SSW041DoublePurification5primetoehold"}
fiveprime_handle_pattern = np.zeros((32,32))
for n in np.arange(16,32):
    if n % 2 == 0: # only place on even slats:
        fiveprime_handle_pattern[(n, 31)] = 1
    else: # nothing on odd numbers
        continue

NQ_mega.assign_cargo_handles_with_array(fiveprime_handle_pattern, doublepure_key, layer='bottom')
allE_mega.assign_cargo_handles_with_array(fiveprime_handle_pattern, doublepure_key, layer='bottom')

NQ_mega.patch_placeholder_handles(plates + cargo_plates)
allE_mega.patch_placeholder_handles(plates  + cargo_plates)

NQ_mega.patch_flat_staples(plates[0])
allE_mega.patch_flat_staples(plates[0])

########## ECHO EXPORT
if generate_echo:
    print('Echo Sheets:')
    echo_sheet1 = convert_slats_into_echo_commands(
        slat_dict=NQ_mega.slats,
        destination_plate_name='ColNQ_plate',
        reference_transfer_volume_nl=75,
        output_folder=echo_folder,
        plate_viz_type='barcode',
        output_filename=f'ColNQ_echo.csv',
        center_only_well_pattern= True, normalize_volumes=True)
    print('--')
    echo_sheet2 = convert_slats_into_echo_commands(
        slat_dict=allE_mega.slats,
        destination_plate_name='allE_plate',
        reference_transfer_volume_nl=75,
        output_folder=echo_folder,
        plate_viz_type='barcode',
        output_filename=f'ColallE_echo.csv',
        center_only_well_pattern= True, normalize_volumes=True)


########## OPTIONAL EXPORTS
if regen_graphics:
    NQ_mega.create_standard_graphical_report(os.path.join(design_folder, 'NQgraphics'))
    allE_mega.create_standard_graphical_report(os.path.join(design_folder, 'allEgraphics'))

if generate_lab_helpers:
    print('Helper Sheets:')
    prepare_all_standard_sheets(NQ_mega.slats, os.path.join(lab_helper_folder, f'ColNQ_standard_helpers.xlsx'),
                                reference_single_handle_volume=75,
                                reference_single_handle_concentration=500,
                                echo_sheet=None if not generate_echo else echo_sheet1,
                                handle_mix_ratio=15, split_core_staple_pools=True,
                                peg_groups_per_layer=2,peg_concentration=3)
    print('--')
    prepare_all_standard_sheets(allE_mega.slats, os.path.join(lab_helper_folder, f'ColallE_standard_helpers.xlsx'),
                                reference_single_handle_concentration=500,
                                reference_single_handle_volume=75,
                                handle_mix_ratio=15, split_core_staple_pools=True,
                                echo_sheet=None if not generate_echo else echo_sheet2,
                                peg_groups_per_layer=2,peg_concentration=3)

if export_design:
    NQ_mega.export_design('full_designH29.xlsx', design_folder)
    allE_mega.export_design('full_designH30.xlsx', design_folder)

design_files_to_combine = [os.path.join(echo_folder, 'ColallE_echo.csv'), os.path.join(echo_folder, 'ColNQ_echo.csv')]
# read in each csv file, combine together and then save to a new output file
combined_csv = pd.concat([pd.read_csv(f) for f in design_files_to_combine])
combined_csv.to_csv(os.path.join(echo_folder, 'combined_echo_colNQallE.csv'), index=False)
