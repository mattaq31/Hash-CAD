import numpy as np
import os

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.helper_functions import create_dir_if_empty
from crisscross.plate_mapping import get_cutting_edge_plates, get_cargo_plates, get_plateclass
from plate_mapping import seed_slat_purification_handles
from plate_mapping.plate_constants import simpsons_mixplate_antihandles, cargo_plate_folder

########## CONFIG

user_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Crisscross Designs/'
design_folder = os.path.join(user_folder, 'YXZ006_Nelson_Quimby_Mats')
NQ_import_file = os.path.join(design_folder, 'colsquareNQ.xlsx')

echo_folder = os.path.join(design_folder, 'additional_nelson_quimby_mats_september_15_2025','echo_commands')
lab_helper_folder = os.path.join(design_folder,'additional_nelson_quimby_mats_september_15_2025', 'lab helpers')

create_dir_if_empty(echo_folder, lab_helper_folder)
generate_echo= True
generate_lab_helpers = True

######### Import
NQ_mega = Megastructure(import_design_file=NQ_import_file)

hamming_NQ = multirule_oneshot_hamming(NQ_mega.generate_slat_occupancy_grid(), NQ_mega.generate_assembly_handle_grid(),
                                                      request_substitute_risk_score=True)

print('Hamming distance from optimized array: %s, Duplication Risk: %s' % (hamming_NQ['Universal'], hamming_NQ['Substitute Risk']))

#PATCHING PLATES
plates= get_cutting_edge_plates(100)
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)
src_007 = get_plateclass('HashCadPlate', simpsons_mixplate_antihandles, cargo_plate_folder)

########## ADDING TOEHOLD CARGO
doublepure_key = {1 : "SSW041DoublePurification5primetoehold"}
fiveprime_handle_pattern = np.zeros((32,32))
for n in np.arange(16,32):
    if n % 2 == 0: # only place on even slats:
        fiveprime_handle_pattern[(n, 31)] = 1
    else: # nothing on odd numbers
        continue

NQ_mega.assign_cargo_handles_with_array(fiveprime_handle_pattern, doublepure_key, layer='bottom')
NQ_mega.patch_placeholder_handles(plates + (src_007, src_004))
NQ_mega.patch_flat_staples(plates[0])

########## ECHO EXPORT
if generate_echo:
    print('Echo Sheets:')
    echo_sheet1 = convert_slats_into_echo_commands(
        slat_dict=NQ_mega.slats,
        destination_plate_name='ColNQ_plate',
        reference_transfer_volume_nl=75,
        output_folder=echo_folder,
        unique_transfer_volume_for_plates={'P3643_MA': 200},
        plate_viz_type='barcode',
        output_filename=f'ColNQ_echo.csv',
        center_only_well_pattern= True, normalize_volumes=True)

########## OPTIONAL EXPORTS
if generate_lab_helpers:
    print('Helper Sheets:')
    prepare_all_standard_sheets(NQ_mega.slats, os.path.join(lab_helper_folder, f'ColNQ_standard_helpers.xlsx'),
                                reference_single_handle_volume=75,
                                reference_single_handle_concentration=500,
                                echo_sheet=None if not generate_echo else echo_sheet1,
                                handle_mix_ratio=15, split_core_staple_pools=True,
                                peg_groups_per_layer=2,peg_concentration=3)

