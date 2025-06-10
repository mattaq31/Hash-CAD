import numpy as np
import os

from crisscross.core_functions.megastructures import Megastructure
from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming

########## CONFIG
experiment_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Papers/hash_cad/exp1_hamming_distance/design_and_echo/Exports'


for file in ['full_designH24.xlsx', 'full_designH27.xlsx', 'full_designH29.xlsx', 'full_designH30.xlsx']:
    full_file = os.path.join(experiment_folder, file)
    H_mega = Megastructure(import_design_file=full_file)
    hamming_results = multirule_oneshot_hamming(H_mega.slat_array, H_mega.handle_arrays, request_substitute_risk_score=True)
    print(file, np.log(-hamming_results['Physics-Informed Partition Score']))
    print('---')

