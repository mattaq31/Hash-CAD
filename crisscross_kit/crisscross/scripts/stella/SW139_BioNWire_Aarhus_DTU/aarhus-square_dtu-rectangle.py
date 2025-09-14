import os
from itertools import product

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.plate_mapping import get_cargo_plates, get_cutting_edge_plates
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets

########################################
# NOTES

# Make two structures for the BioNWire collaboration project
# 1. DTU rectangle - no handles, just approximately the same size as requested
# 2. Aarhus square - similar design as SW131, only 5-slat and 6-slat gaps,
# but now with an added 3rd layer for security
# Both have secondary purification handles

########################################
# SETUP

design_folder = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW139_BioNWire_shipments'
echo_folder = os.path.join(design_folder, 'echo_commands')
lab_helper_folder = os.path.join(design_folder, 'lab_helper_sheets')
create_dir_if_empty(echo_folder, lab_helper_folder)

generate_graphical_report = True
generate_echo = True
generate_lab_helpers = True
compute_hamming = True
new_sequence_plate_generation = False
export_trench_design = True
target_volume = 75 # nL
example_concentration = 500 # µM

main_plates = get_cutting_edge_plates(100) # This sets the concentration to 100 µM, tho the plate_concentrations.py file still has 500 µM
src_004, src_005, src_007, P3518, P3510, P3628 = get_cargo_plates()

########################################
# Make DTU rectangles
rectangle = Megastructure(import_design_file=os.path.join(design_folder, 'dtu_rectangle_placement.xlsx'))
rectangle.patch_placeholder_handles(main_plates + (src_004, P3510,))
rectangle.patch_flat_staples(main_plates[0])

echo_sheet_dtu = convert_slats_into_echo_commands(slat_dict=rectangle.slats,
                                                        destination_plate_name='bionwire_dtu_rectangle',
                                                        reference_transfer_volume_nl=target_volume,
                                                        reference_concentration_uM=example_concentration,
                                                        output_folder=echo_folder,
                                                        plate_viz_type='barcode',
                                                        normalize_volumes=True,
                                                        output_filename=f'SW139_bionwire_dtu-rectangle_echo.csv')

if generate_lab_helpers:
    prepare_all_standard_sheets(rectangle.slats, os.path.join(lab_helper_folder, 'SW139_bionwire_dtu-rectangle_helpers.xlsx'),
                                    reference_single_handle_volume=target_volume,
                                    reference_single_handle_concentration=example_concentration,
                                    echo_sheet=None if not generate_echo else echo_sheet_dtu,
                                    handle_mix_ratio=10, # setting to 15 to be able to setup the reaction inside the echo plate itself
                                    slat_mixture_volume=100,
                                    peg_concentration=2,
                                    peg_groups_per_layer=2)

########################################
# Make Aarhus squares
# Actually, both are really the same design, just that the gap 6 is misssing one more slat
# This slat will be individually PEGed and folded at a higher volume


design_file = "aarhus_square_3layer_trench_5gap.xlsx"
square = Megastructure(import_design_file=os.path.join(design_folder, design_file))
square.patch_placeholder_handles(main_plates + (src_004, P3510,))
square.patch_flat_staples(main_plates[0])

echo_sheet_aarhus = convert_slats_into_echo_commands(slat_dict=square.slats,
                                                    destination_plate_name='bionwire_aarhus_square_5gap',
                                                    reference_transfer_volume_nl=target_volume,
                                                    reference_concentration_uM=example_concentration,
                                                    output_folder=echo_folder,
                                                    plate_viz_type='barcode',
                                                    normalize_volumes=True,
                                                    output_filename='SW139_bionwire_aarhus-square_5gap_echo.csv')

# I manually made an extra copy of G6, which is layer3-slat19, the slat that gap5 has but gap6 does not

if generate_lab_helpers:
    prepare_all_standard_sheets(square.slats, os.path.join(lab_helper_folder, 'SW139_bionwire_aarhus-square_helpers.xlsx'),
                                reference_single_handle_volume=target_volume,
                                reference_single_handle_concentration=example_concentration,
                                echo_sheet=None if not generate_echo else echo_sheet_aarhus,
                                handle_mix_ratio=10, # setting to 15 to be able to setup the reaction inside the echo plate itself
                                slat_mixture_volume=100,
                                peg_concentration=2,
                                peg_groups_per_layer=2)