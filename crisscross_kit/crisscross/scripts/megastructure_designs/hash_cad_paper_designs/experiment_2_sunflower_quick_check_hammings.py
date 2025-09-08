import numpy as np
import os

from crisscross.core_functions.megastructures import Megastructure
from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming

########## CONFIG
experiment_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Papers/hash_cad/exp2_handle_library_sunflowers/design_stuff/'


for version in range(6):
    if version == 0:
        full_file = os.path.join(experiment_folder, 'v0_with_gnps', f'v0_with_gnps_design.xlsx')
    else:
        full_file = os.path.join(experiment_folder, 'v%s' % version, f'v{version}_design.xlsx')

    H_mega = Megastructure(import_design_file=full_file)
    hamming_results = multirule_oneshot_hamming(H_mega.generate_slat_occupancy_grid(), H_mega.generate_assembly_handle_grid(), request_substitute_risk_score=True)
    print(f'v{version}', hamming_results['Universal'], np.log(-hamming_results['Physics-Informed Partition Score']))
    print('---')

