import os
import pandas as pd
import copy

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates, get_plateclass
from crisscross.plate_mapping.plate_constants import seed_slat_purification_handles, cargo_plate_folder, simpsons_mixplate_antihandles_maxed, cnt_patterning_2


########################################
# NOTES

# Make 3 structures in total:
# SW143 - Checkpoint handle post-assembly purification structure (this is the most "normal" of the designs)
# SW146 - H30 square for U Fribourg collaborators, with very many cargo handles (note that Atto532 and Atto647 are not available, need to specify manual addition)
# SW149 - Kinetics assay with slat duplexes (6 slats total, but attachment is all across the slat rather than at crisscrossing points, also has fluorescent staples that need to be manual)

########################################
# General stuff

main_plates = get_cutting_edge_plates(200) # New working stocks are at 200 uM
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)
src_010 = get_plateclass('HashCadPlate', simpsons_mixplate_antihandles_maxed, cargo_plate_folder)
P3837 = get_plateclass('HashCadPlate', cnt_patterning_2, cargo_plate_folder)  # U Fribourg CNT patterning plate 2

design_folder_prefix = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/'
generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True

########################################
# SW143
design_folder_SW143 = os.path.join(design_folder_prefix, 'SW143_postassembly_purification')
echo_folder_SW143 = os.path.join(design_folder_SW143, 'echo_commands')
lab_helper_folder_SW143 = os.path.join(design_folder_SW143, 'lab_helper_sheets')
create_dir_if_empty(echo_folder_SW143, lab_helper_folder_SW143)

### --- Make structures --- ###
print("Making SW143 Megastructure...")
long_snake = Megastructure(import_design_file=os.path.join(design_folder_SW143, 'checkpoint_handles_design_k64_h4.xlsx'))
long_snake.patch_placeholder_handles(main_plates + (src_004,))
long_snake.patch_flat_staples(main_plates[0])

########################################
# SW146
design_folder_SW146 = os.path.join(design_folder_prefix, 'SW146_UFribourg_Design4')
echo_folder_SW146 = os.path.join(design_folder_SW146, 'echo_commands')
lab_helper_folder_SW146 = os.path.join(design_folder_SW146, 'lab_helper_sheets')
create_dir_if_empty(echo_folder_SW146, lab_helper_folder_SW146)

### --- Make structures --- ###
print("Making SW146 Megastructure...")
fribourg_sq = Megastructure(import_design_file=os.path.join(design_folder_SW146, 'design4_fullcargo.xlsx'))
fribourg_sq.patch_placeholder_handles(main_plates + (src_004, src_010, P3837,))
fribourg_sq.patch_flat_staples(main_plates[0])

########################################
# SW149
design_folder_SW149 = os.path.join(design_folder_prefix, 'SW149_kinetics_duplex')
echo_folder_SW149 = os.path.join(design_folder_SW149, 'echo_commands')
lab_helper_folder_SW149 = os.path.join(design_folder_SW149, 'lab_helper_sheets')
create_dir_if_empty(echo_folder_SW149, lab_helper_folder_SW149)

### --- Make structures --- ###
print("Making SW149 Megastructure...")
kinetics_duplex = Megastructure(import_design_file=os.path.join(design_folder_SW149, 'kinetics_duplex.xlsx'))
kinetics_duplex.patch_placeholder_handles(main_plates + (P3837,))
kinetics_duplex.patch_flat_staples(main_plates[0])

########################################
# Prepare echo instructions, for SW143 independently, then put SW146 and SW149 on the same plate

# SW143
target_volume_SW143 = 75
target_concentration_SW143 = 500
print("Writing SW143 echo instructions...")
echo_sheet_SW143 = convert_slats_into_echo_commands(slat_dict=long_snake.slats,
                                                        destination_plate_name='post-assembly_purification',
                                                        reference_transfer_volume_nl=target_volume_SW143,
                                                        reference_concentration_uM=target_concentration_SW143,
                                                        center_only_well_pattern=False,
                                                        output_folder=echo_folder_SW143,
                                                        plate_viz_type='barcode',
                                                        normalize_volumes=True,
                                                        output_filename='{}_{}.csv'.format("SW143", 'post-assembly_purification'))

prepare_all_standard_sheets(long_snake.slats, os.path.join(lab_helper_folder_SW143, '{}_{}.xlsx'.format("SW143", 'post-assembly_purification')),
                            reference_single_handle_volume=target_volume_SW143,
                            reference_single_handle_concentration=target_concentration_SW143,
                            echo_sheet=None if not generate_echo else echo_sheet_SW143,
                            handle_mix_ratio=10, 
                            slat_mixture_volume=100,
                            peg_concentration=2,
                            peg_groups_per_layer=4)

# SW146
target_volume_SW146 = 125
target_concentration_SW146 = 500
print("Writing SW146 echo instructions...")
echo_sheet_SW146 = convert_slats_into_echo_commands(slat_dict=fribourg_sq.slats,
                                                    destination_plate_name=f'fribourg_design4',
                                                    reference_transfer_volume_nl=target_volume_SW146,
                                                    reference_concentration_uM=target_concentration_SW146,
                                                    center_only_well_pattern=True,
                                                    output_folder=echo_folder_SW146,
                                                    plate_viz_type='barcode',
                                                    normalize_volumes=True,
                                                    output_filename='{}_{}.csv'.format("SW146", 'fribourg_design4'),
                                                    output_empty_wells=True)

# Skip the lab helper sheets because the placeholder handles will mess this up

# Need to make SW149 slats at 200 µL total reaction volume for successful PEG, so add this to a separate plate for now
# Put SW149 wells on the same plate as the Fribourg square - just use the same plate name
target_volume_SW149 = 125
target_concentration_SW149 = 500

kinetics_assay_well_ordering ={"layer1-slat1" : 3, "layer1-slat2" : 5, \
                               "layer1-slat129" : 4, "layer1-slat130" : 6, \
                                "layer2-slat1" : 7, "layer2-slat2" : 8}
plate_rows = ['A', 'B', 'C'] # 3 replicates
kinetics_assay_wells = {}
kinetic_slats_for_echo = {}

for i, row in enumerate(plate_rows):
    for slat_id in kinetics_duplex.slats.keys():
        # Assign well for each slat
        kinetics_assay_wells[slat_id + '-R{}'.format(i+1)] = (1, f"{row}{kinetics_assay_well_ordering[slat_id]}")

        # Add slat to the well dictionary for echo
        kinetic_slats_for_echo[slat_id + '-R{}'.format(i+1)] = copy.deepcopy(kinetics_duplex.slats[slat_id])
        kinetic_slats_for_echo[slat_id + '-R{}'.format(i+1)].ID = slat_id + '-R{}'.format(i+1)


print("Writing SW149 echo instructions...")
echo_sheet_SW149 = convert_slats_into_echo_commands(slat_dict=kinetic_slats_for_echo,
                                                    destination_plate_name=f'kinetics_duplex',
                                                    reference_transfer_volume_nl=target_volume_SW149,
                                                    reference_concentration_uM=target_concentration_SW149,
                                                    center_only_well_pattern=False,
                                                    manual_plate_well_assignments=kinetics_assay_wells,
                                                    output_folder=echo_folder_SW149,
                                                    plate_viz_type='barcode',
                                                    normalize_volumes=True,
                                                    output_filename='{}_{}.csv'.format("SW149", 'kinetics_duplex'),
                                                    output_empty_wells=True)

# Skip the lab helper sheets because the placeholder handles will mess this up

# Combine all echo instructions
design_files_to_combine = [os.path.join(echo_folder_SW143, 'SW143_post-assembly_purification.csv'),
                           os.path.join(echo_folder_SW146, 'SW146_fribourg_design4.csv'),
                           os.path.join(echo_folder_SW149, 'SW149_kinetics_duplex.csv')]

# read in each csv file, combine together and then save to a new output file
combined_csv = pd.concat([pd.read_csv(f) for f in design_files_to_combine])

combined_csv.to_csv(os.path.join(echo_folder_SW149, "SW143_SW146_SW149_combined_echo.csv"), index=False)