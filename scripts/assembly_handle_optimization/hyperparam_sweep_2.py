import copy
import numpy as np
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.slurm_process_and_run import create_o2_slurm_file
import os
import toml

# this file generates configs for various hyperparameter tests

root_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/assembly_handle_optimization'
design_folder = os.path.join(root_folder, 'slat_designs')
batch_file_folder = os.path.join(root_folder, 'experiment_folders')
server_base_folder = '/home/maa2818/hamming_optimization_experiments'
create_dir_if_empty(design_folder, batch_file_folder)

slurm_parameters = {
    'num_cpus': 20,
    'memory': 32,
    'time_length': 6,
}

default_evolution_params = {
    'early_hamming_stop': 31,
    'evolution_generations': 2000,
    'evolution_population': 300,
    'process_count': 18,
    'generational_survivors': 5,
    'mutation_rate': 0.03,
    'slat_length': 32,
    'unique_handle_sequences': 32,
    'split_sequence_handles': False,
    'mutation_type_probabilities': (0.425, 0.425, 0.15),
    'progress_bar_update_iterations': 10,
    'random_seed': 8,
}

design_1 = 'basic_square.xlsx'
server_design_folder = os.path.join(server_base_folder, 'slat_designs')
default_evolution_params['slat_array'] = os.path.join(server_design_folder, design_1)

all_sbatch_commands = []

# MUTATION RATE VS EVOLUTION POPULATION
group_name = 'mutation_vs_evo_pop_sweep'

for mutation_rate in [0.0001, 0.001, 0.005, 0.01, 0.02, 0.03, 0.05, 0.1, 0.2]:
    for ev_pop in range(10, 500, 50):
        exp_name = f'base_square_{mutation_rate:.4f}_mut_rate_{ev_pop}_evo_population'
        exp_params = copy.copy(default_evolution_params)
        server_experiment_folder = os.path.join(server_base_folder, 'experiment_folders', group_name, exp_name)
        server_toml_file = os.path.join(server_experiment_folder, 'evolution_config.toml')
        output_folder = os.path.join(batch_file_folder, group_name, exp_name)
        create_dir_if_empty(output_folder)

        exp_params['mutation_rate'] = float(mutation_rate)
        exp_params['evolution_population'] = ev_pop
        exp_params['log_tracking_directory'] = server_experiment_folder

        with open(os.path.join(output_folder, 'evolution_config.toml'), "w") as f:
            toml.dump(exp_params, f)

        slurm_batch = create_o2_slurm_file(**slurm_parameters, command=f'handle_evolve -c {server_toml_file}')
        slurm_file  = os.path.join(output_folder, 'server_call.sh')
        server_slurm_file = os.path.join(server_experiment_folder, 'server_call.sh')

        with open(slurm_file, 'w') as f:  # writes batch file out for use
            for line in slurm_batch:
                f.write(line)

        all_sbatch_commands.append(f'sbatch {server_slurm_file}\n')

with open(os.path.join(batch_file_folder, 'slurm_queue_gen_2.sh'), 'w') as f:  # writes batch file out for use
    for line in all_sbatch_commands:
        f.write(line)

