# very quick cost calculations used for a presentation to estimate how much a new handle library would cost to purchase

from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming
from crisscross.core_functions.megastructures import Megastructure
from crisscross.plate_mapping import get_standard_plates
from collections import defaultdict
import os

# handle library calculations
core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, _, _, _, all_8064_seed_plugs = get_standard_plates(
    handle_library_v2=True)


total_seqs = defaultdict(int)

for side in [2, 5]:
    for pos in range (1,33):
        total_seqs[side] += len(core_plate.sequences[pos, side, 0])

total_bases = 0
for seq in crisscross_handle_x_plates.sequences.values():
    total_bases += len(seq)

total_bases_y = 0
for seq in crisscross_antihandle_y_plates.sequences.values():
    total_bases_y += len(seq)

bases_from_library = 9 * 2048
bases_for_scaffold = total_bases - bases_from_library
bases_for_scaffold_y = total_bases_y - bases_from_library
total_scaf_bases = bases_for_scaffold_y + bases_for_scaffold

# single design calculations

base_design_import_file = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/optical_computers/design_mar_2025/full_design.xlsx'

########## LOADING AND CHECKING DESIGN
megastructure = Megastructure(import_design_file=base_design_import_file)
optimized_hamming_results = multirule_oneshot_hamming(megastructure.slat_array, megastructure.handle_arrays, request_substitute_risk_score=True)
print('Hamming distance from optimized array: %s, Duplication Risk: %s' % (optimized_hamming_results['Universal'], optimized_hamming_results['Substitute Risk']))

megastructure.patch_placeholder_handles(
    [crisscross_handle_x_plates, crisscross_antihandle_y_plates],
    ['Assembly-Handles', 'Assembly-AntiHandles'])

assembly_handle_dict = defaultdict(list)
plate_set = set()
for slat in megastructure.slats.values():
    for side in [slat.H2_handles, slat.H5_handles]:
        for handle in side.values():
            if 'Assembly-' in handle['descriptor']:
                assembly_handle_dict[f"{handle['well']}-{handle['plate']}"] = len(handle['sequence'])
                plate_set.add(handle['plate'])

total_seq_length = 0
for a in assembly_handle_dict.values():
    total_seq_length += a
