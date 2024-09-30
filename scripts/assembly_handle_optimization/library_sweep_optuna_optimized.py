from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.slurm_process_and_run import create_o2_slurm_file
import os
import toml

# will be testing the impact of improving the library size from 16 -32 for the square design
# evolution parameters used will be the Optuna ones

root_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/assembly_handle_optimization'
design_folder = os.path.join(root_folder, 'slat_designs')
batch_file_folder = os.path.join(root_folder, 'experiment_folders', 'optuna_params_library_sweep')
server_base_folder = '/home/maa2818/hamming_optimization_experiments'
create_dir_if_empty(design_folder, batch_file_folder)

slurm_parameters = {
    'num_cpus': 20,
    'memory': 16,
    'time_length': 72,
}

evolution_parameters = {
    'early_hamming_stop': 31,
    'evolution_generations': 20000,
    'evolution_population': 943,
    'process_count': 20,
    'generational_survivors': 2,
    'mutation_rate': 0.01427,
    'slat_length': 32,
    'unique_handle_sequences': 32,
    'split_sequence_handles': False,
    'mutation_type_probabilities': (0.314, 0.314, 0.372),
    'progress_bar_update_iterations': 10,
    'random_seed': 8,
}

design_1 = 'basic_square.xlsx'

all_sbatch_commands = []

for library_count in range(16, 33):
    server_experiment_folder = os.path.join(server_base_folder, f'experiment_folders/optuna_params_library_sweep/base_square_{library_count}_handle_library')
    server_design_folder = os.path.join(server_base_folder, 'slat_designs')
    server_toml_file = os.path.join(server_experiment_folder, 'evolution_config.toml')
    output_folder = os.path.join(batch_file_folder, f'base_square_{library_count}_handle_library')
    create_dir_if_empty(output_folder)

    evolution_parameters['unique_handle_sequences'] = library_count
    evolution_parameters['log_tracking_directory'] = server_experiment_folder
    evolution_parameters['slat_array'] = os.path.join(server_design_folder, design_1)

    with open(os.path.join(output_folder, 'evolution_config.toml'), "w") as f:
        toml.dump(evolution_parameters, f)

    slurm_batch = create_o2_slurm_file(**slurm_parameters, command=f'handle_evolve -c {server_toml_file}')
    slurm_file  = os.path.join(output_folder, 'server_call.sh')
    server_slurm_file = os.path.join(server_experiment_folder, 'server_call.sh')

    with open(slurm_file, 'w') as f:  # writes batch file out for use
        for line in slurm_batch:
            f.write(line)

    all_sbatch_commands.append(f'sbatch {server_slurm_file}\n')

with open(os.path.join(batch_file_folder, 'slurm_queue_gen_3.sh'), 'w') as f:  # writes batch file out for use
    for line in all_sbatch_commands:
        f.write(line)

