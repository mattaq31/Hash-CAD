import os
import copy
from string import ascii_uppercase
from collections import defaultdict

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.plate_mapping import get_cutting_edge_plates, get_plateclass
from crisscross.plate_mapping.plate_constants import seed_slat_purification_handles, cargo_plate_folder

########## CONFIG
# update these depending on user
experiment_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Papers/double_barrels/design_library/DB Seeded Ribbon'
echo_folder = os.path.join(experiment_folder, 'echo')
lab_helper_folder = os.path.join(experiment_folder, 'lab_helpers')
python_graphics_folder = os.path.join(experiment_folder, 'python_graphics')
create_dir_if_empty(echo_folder, lab_helper_folder, python_graphics_folder)

design_file_unseeded = os.path.join(experiment_folder, 'designs', 'DB-90 Simple Ribbon 9-34, 23-40, 30-58 atto647.xlsx')
design_file_seeded = os.path.join(experiment_folder, 'designs', 'DB-90 Simple Ribbon DB-seeded 9-34, 23-40 atto647.xlsx')

########## LOADING DESIGNS
mega_seeded = Megastructure(import_design_file=design_file_seeded)
mega_unseeded = Megastructure(import_design_file=design_file_unseeded)

generate_echo = True

main_plates = get_cutting_edge_plates(200)
src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)

valency_results = mega_seeded.get_parasitic_interactions()
print(f'Parasitic interactions for seeded ribbon - Max valency: {valency_results["worst_match_score"]}, effective valency: {valency_results["mean_log_score"]}')
valency_results = mega_unseeded.get_parasitic_interactions()
print(f'Parasitic interactions for unseeded ribbon - Max valency: {valency_results["worst_match_score"]}, effective valency: {valency_results["mean_log_score"]}')

for m, design_name in zip([mega_seeded, mega_unseeded], ['seeded_ribbon', 'unseeded_ribbon']):
    m.patch_placeholder_handles(main_plates + (src_004,))
    m.patch_flat_staples(main_plates[0]) # this plate contains only flat staples

    for s_id, slat in m.slats.items():
        if slat.slat_type == 'DB-L':
            slat.H2_handles[16]['category'] = 'SKIP'
            slat.H5_handles[16]['category'] = 'SKIP'

    # Repeating unit slats will have special handles for fluorescent labelling (handle 58 pos 30 and 2)
    # These need to be handled manually
    for slat_id, slat in m.slats.items():
        for handle_id, handle in slat.H5_handles.items():
            if (slat_id, handle_id, 5) in m.link_manager.handle_link_to_group:
                group_val = m.link_manager.handle_link_to_group[(slat_id, handle_id, 5)]
                if group_val in m.link_manager.handle_group_to_value:
                    handle['category'] = 'SKIP'

    if design_name == 'unseeded_ribbon':
        duplicate_count = 3
    else:
        duplicate_count = 2

    slats_with_dups = {}
    for s_id, s in m.slats.items():
        if s.phantom_parent is not None:
            continue
        for d in range(duplicate_count):
            slats_with_dups[f'{s_id}-{d+1}'] = copy.deepcopy(s)
            slats_with_dups[f'{s_id}-{d+1}'].ID = f'{s_id}-{d+1}'

    # Build manual_plate_well_assignments to group slats by fleet and layer
    # Organization: each fleet (duplicate number) gets its own section, within which each layer gets its own row
    # Group slats by fleet (duplicate number) and layer
    fleet_layer_groups = defaultdict(lambda: defaultdict(list))
    for slat_id, slat in slats_with_dups.items():
        if slat.phantom_parent is not None:
            continue
        # Extract fleet number from suffix (e.g., 'layer1-slat1-2' -> fleet 2)
        fleet_num = int(slat_id.rsplit('-', 1)[1])
        fleet_layer_groups[fleet_num][slat.layer].append(slat_id)

    # Assign wells row by row
    manual_plate_well_assignments = {}
    current_row = 0
    plate_num = 1
    max_cols = 12  # 96-well plate has 12 columns per row
    max_rows = 8   # 96-well plate has 8 rows (A-H)

    for fleet_num in sorted(fleet_layer_groups.keys()):
        for layer in sorted(fleet_layer_groups[fleet_num].keys()):
            slat_ids = fleet_layer_groups[fleet_num][layer]
            col = 2
            for slat_id in slat_ids:
                if col >= max_cols:
                    # Move to next row if current row is full
                    current_row += 1
                    col = 2
                if current_row >= max_rows:
                    # Move to next plate if current plate is full
                    plate_num += 1
                    current_row = 0
                well = f'{ascii_uppercase[current_row]}{col + 1}'
                manual_plate_well_assignments[slat_id] = (plate_num, well)
                col += 1
            # After each layer, move to the next row
            current_row += 1
            if current_row >= max_rows:
                plate_num += 1
                current_row = 0

    if generate_echo:
        commands_barrels = convert_slats_into_echo_commands(slat_dict=slats_with_dups,
                                                                  destination_plate_name=f'zigzag_{design_name}',
                                                                  reference_transfer_volume_nl=75,
                                                                  output_folder=echo_folder,
                                                                  center_only_well_pattern=False,
                                                                  plate_viz_type='barcode',
                                                                  normalize_volumes=True,
                                                                  manual_plate_well_assignments=manual_plate_well_assignments,
                                                                  output_filename=f'zigzag_{design_name}_echo.csv')

        prepare_all_standard_sheets(slats_with_dups, os.path.join(lab_helper_folder, f'zigzag_{design_name}_helpers.xlsx'),
                                    reference_single_handle_volume=75,
                                    reference_single_handle_concentration=500,
                                    echo_sheet=commands_barrels,
                                    handle_mix_ratio=15,
                                    slat_mixture_volume=50,
                                    peg_concentration=3,
                                    split_core_staple_pools=True,
                                    peg_groups_per_layer=2)
