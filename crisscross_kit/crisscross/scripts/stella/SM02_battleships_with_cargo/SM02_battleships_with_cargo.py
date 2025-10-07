import os
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cargo_plates, get_cutting_edge_plates

########## CONFIG
# update these depending on user
experiment_folder = '/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SM02_hexagon_battleships_with_cargo'

target_designs = ['sera_battleship_design_cross_seam', "sera_battleship_design_along_seam", "sera_battleship_design_parallel_variations"]

base_design_import_files = [os.path.join(experiment_folder, f"{f}.xlsx") for f in target_designs]
regen_graphics = False
generate_echo = True
generate_lab_helpers = True

main_plates = get_cutting_edge_plates()
cargo_plates = get_cargo_plates()

row = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

########## LOADING AND CHECKING DESIGN
for i, (file, design_name) in enumerate(zip(base_design_import_files, target_designs)):

    echo_folder = os.path.join(experiment_folder, design_name, 'echo_commands')
    lab_helper_folder = os.path.join(experiment_folder, design_name, 'lab_helper_sheets')
    create_dir_if_empty(echo_folder, lab_helper_folder)
    print('%%%%%%%%%%%%%%%')
    print('ASSESSING DESIGN: %s' % design_name)

    megastructure = Megastructure(import_design_file=file)
    hamming_results = multirule_oneshot_hamming(megastructure.generate_slat_occupancy_grid(), megastructure.generate_assembly_handle_grid(), request_substitute_risk_score=True)
    print('Hamming distance from imported array: %s, Duplication Risk: %s' % (hamming_results['Universal'], hamming_results['Substitute Risk']))

    ########## PATCHING PLATES
    megastructure.patch_placeholder_handles(main_plates + cargo_plates)
    megastructure.patch_flat_staples(main_plates[0])

    target_volume = 75 # nl per staple
    if generate_echo:
        # Only save layer 3 slats
        exported_slats = {}
        for slatname in megastructure.slats.keys():
            if "layer3" in slatname:
                exported_slats[slatname] = megastructure.slats[slatname]
        # Prepare the specific wells
        manual_wells = [(1, row[i]+str(x+1)) for x in range(len(exported_slats))]

        echo_sheet_1 = convert_slats_into_echo_commands(exported_slats,
                                     destination_plate_name="battleships_with_cargo",
                                     manual_plate_well_assignments=manual_wells,
                                     reference_transfer_volume_nl=target_volume,
                                     output_folder=echo_folder,
                                     center_only_well_pattern=False,
                                     plate_viz_type='barcode',
                                     output_filename=f'{design_name}_echo_commands.csv')
