from crisscross.slat_handle_match_evolver import generate_random_slat_handles
from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming
from crisscross.core_functions.slat_design import generate_standard_square_slats
import numpy as np
from sko.PSO import PSO
import pandas as pd

slat_array, unique_slats_per_layer = generate_standard_square_slats(32)  # standard square
handle_array = generate_random_slat_handles(slat_array, 32)

example_design = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/optical_computers/design_with_2_step_purif_oct_2024/full_design.xlsx'
example_design = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/assembly_handle_optimization/experiment_folders/optuna_hyperparam_finding/trial_322/best_handle_array_generation_40.xlsx'
design_df = pd.read_excel(example_design, sheet_name=None, header=None)
initial_handle_array = np.zeros((design_df['handle_interface_1'].shape[0], design_df['handle_interface_1'].shape[1], 1))
for i, key in enumerate(design_df.keys()):
    if 'handle_interface_' not in key:
        continue
    initial_handle_array[..., 0] = design_df[key].values

z = multirule_oneshot_hamming(slat_array, initial_handle_array, per_layer_check=True, report_worst_slat_combinations=True, request_substitute_risk_score=True)

def optim_fn(handle_vector):

    ha = np.zeros((slat_array.shape[0], slat_array.shape[1], slat_array.shape[2] - 1), dtype=np.int32)

    for index, element in enumerate(handle_vector):
        ha[index // slat_array.shape[1], index % slat_array.shape[1], 0] = element

    score_dict = multirule_oneshot_hamming(slat_array, ha,
                                           per_layer_check=False, report_worst_slat_combinations=False,
                                           request_substitute_risk_score=False)

    return np.log10(-score_dict['Physics-Informed Partition Score'])

handle_vector = handle_array.flatten()
pso = PSO(func=optim_fn, n_dim=32*32, pop=40, max_iter=300, lb=[1]*32*32, ub=[32]*32*32, w=0.8, c1=0.5, c2=0.5, verbose=True)
pso.run()

fin_ha = np.zeros((slat_array.shape[0], slat_array.shape[1], slat_array.shape[2] - 1), dtype=np.int32)
for index, element in enumerate(pso.gbest_x):
    fin_ha[index // slat_array.shape[1], index % slat_array.shape[1], 0] = element

rx = multirule_oneshot_hamming(slat_array, fin_ha, per_layer_check=True, report_worst_slat_combinations=True, request_substitute_risk_score=True)
print(rx)
print('best_x is ', pso.gbest_x, 'best_y is', pso.gbest_y)
