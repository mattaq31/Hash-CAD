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
design_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/hash_cad_validation_designs/2d_hc_ribbon/'
design_file = 'S24_paper_ribbon_evolved.xlsx'

echo_folder = os.path.join(design_folder, 'echo')
create_dir_if_empty(echo_folder)

mega = Megastructure(import_design_file=os.path.join(design_folder, design_file))

valency_results = mega.get_parasitic_interactions()
print(f'Max valency: {valency_results["worst_match_score"]}, effective valency: {valency_results["mean_log_score"]}')

main_plates = get_cutting_edge_plates(200)
mega.patch_placeholder_handles(main_plates)
mega.patch_flat_staples(main_plates[0])

echo_sheet_1 = convert_slats_into_echo_commands(slat_dict=mega.slats,
                                                destination_plate_name=f'test',
                                                reference_transfer_volume_nl=50,
                                                output_folder=echo_folder,
                                                output_empty_wells=True,
                                                center_only_well_pattern=True,
                                                plate_viz_type='barcode',
                                                output_filename=f'echo_basic.csv')
