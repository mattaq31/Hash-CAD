import numpy as np
import os

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming
from crisscross.core_functions.slats import Slat
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.plate_constants import plate96_center_pattern
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates

########## CONFIG
experiment_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/optical_computers/design_with_2_step_purif_oct_2024'
base_design_import_file = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/optical_computers/design_aug_2024/full_design.xlsx'
echo_folder = os.path.join(experiment_folder, 'echo_commands')
create_dir_if_empty(echo_folder)
regen_graphics = False
export_design = True

########## LOADING AND CHECKING DESIGN
megastructure = Megastructure(import_design_file=base_design_import_file)
optimized_hamming_results = multirule_oneshot_hamming(megastructure.slat_array, megastructure.handle_arrays,
                                                      request_substitute_risk_score=True)
print('Hamming distance from optimized array: %s, Duplication Risk: %s' % (optimized_hamming_results['Universal'], optimized_hamming_results['Substitute Risk']))
########## ADDING TOEHOLD CARGO
doublepure_key = {1 : "SSW041DoublePurification5primetoehold"}
fiveprime_handle_pattern = np.zeros((32,32))
for n in np.arange(16,32):
    if n % 2 == 0: # only place on even slats:
        fiveprime_handle_pattern[(n, 31)] = 1
    else: # nothing on odd numbers
        continue
megastructure.assign_cargo_handles_with_array(fiveprime_handle_pattern, doublepure_key, layer='bottom')
########## PATCHING PLATES
core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate = get_standard_plates()
src_004, src_005, src_007, P3518 = get_cargo_plates()

megastructure.patch_placeholder_handles(
    [crisscross_handle_x_plates, crisscross_antihandle_y_plates, combined_seed_plate, src_007, P3518, src_004],
    ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo', 'Cargo'])

megastructure.patch_control_handles(core_plate)
########## ADDING AN ADDITIONAL SLAT FOR TESTING STAPLE RECYCLING
# custom slat for crossbar system
staple_recycling_slat = Slat('staple_recycling_slat', 0, 'N/A')
for i in range(32):
    if i ==0 or i == 31:
        if i == 0:
            cargo_id = 'antiNelson'
        else:
            cargo_id = 'antiQuimby'
        seq = src_007.get_sequence(i + 1, 2, cargo_id)
        well = src_007.get_well(i + 1, 2, cargo_id)
        plate = src_007.get_plate_name(i + 1, 2, cargo_id)
        descriptor = 'Cargo Plate %s, Fluoro Handle %s' % (src_007.get_plate_name(), cargo_id)
        staple_recycling_slat.set_handle(i + 1, 2, seq, well, plate, descriptor=descriptor)
    else:
        seq = core_plate.get_sequence(i + 1, 2, 0)
        well = core_plate.get_well(i + 1, 2, 0)
        plate = core_plate.get_plate_name(i + 1, 2, 0)
        staple_recycling_slat.set_handle(i + 1, 2, seq, well, plate, descriptor='Empty')

    seq = core_plate.get_sequence(i + 1, 5, 0)
    well = core_plate.get_well(i + 1, 5, 0)
    plate = core_plate.get_plate_name(i + 1, 5, 0)
    staple_recycling_slat.set_handle(i + 1, 5, seq, well, plate, descriptor='Empty')
########## ECHO EXPORT

precise_well_placement = plate96_center_pattern
precise_well_placement.append('H11')
full_well_placement = [(1, well) for well in precise_well_placement]

convert_slats_into_echo_commands(slat_dict={**megastructure.slats, **{'staple_recycling_slat': staple_recycling_slat}},
                                 destination_plate_name='octa_double_purif_plate',
                                 unique_transfer_volume_for_plates={'sw_src007': int(150 * (500 / 200)),
                                                                    'sw_src004': int(150 * (500 / 200)),
                                                                    'P3518_MA': int(150 * (500 / 200))},
                                 default_transfer_volume=150,
                                 transfer_volume_multiplier_for_slats={'staple_recycling_slat': 2},
                                 output_folder=echo_folder,
                                 manual_plate_well_assignments=full_well_placement,
                                 plate_viz_type='barcode',
                                 output_filename=f'columbia_pattern_2_step_purif_echo.csv')

########## OPTIONAL EXPORTS
if regen_graphics:
    megastructure.create_standard_graphical_report(os.path.join(experiment_folder, 'graphics'))
if export_design:
    megastructure.export_design('full_design.xlsx', experiment_folder)

########## Side-Check for MW
all_handle_seqs = []
all_handle_mws = []
handle_mix_volume = 15
handle_mix_conc = 7462.686567
base_mws = {'A': 313.2, 'C': 289.2, 'G': 329.2, 'T': 304.2}

for handle in staple_recycling_slat.H2_handles.values():
    all_handle_seqs.append(handle['sequence'])
for handle in staple_recycling_slat.H5_handles.values():
    all_handle_seqs.append(handle['sequence'])

for handle in all_handle_seqs:
    mw = 0
    for base in handle:
        mw += base_mws[base.upper()]
    all_handle_mws.append(mw)

all_handle_nmoles = []
all_handle_ngs = []
for mw in all_handle_mws:
    nmoles = handle_mix_volume * handle_mix_conc * 1e-6
    all_handle_nmoles.append(nmoles)
    all_handle_ngs.append(nmoles * mw/handle_mix_volume)

print('Expected nanodrop conc (ng/ul,  ssDNA):', sum(all_handle_ngs))
