from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.slurm_process_and_run import create_o2_slurm_file
import os
import toml


##CHANGE AS NECESSARY!!!
root_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/3D_stacking'
design_folder = root_folder
batch_file_folder = os.path.join(root_folder, 'attempt_1_32_seq_library')
server_base_folder = '/home/maa2818/3d_stacking_optimization'

create_dir_if_empty(design_folder, batch_file_folder)

slurm_parameters = {
    'num_cpus': 20,
    'memory': 16,
    'time_length': 24,
}

evolution_parameters = {
    'early_hamming_stop': 31,
    'evolution_generations': 20000,
    'evolution_population': 300,
    'process_count': 18,
    'generational_survivors': 5,
    'mutation_rate': 0.03,
    'slat_length': 32,
    'unique_handle_sequences': 32,
    'split_sequence_handles': True,
    'progress_bar_update_iterations': 10,
    'random_seed': 8,
}

design_1 = 'design_with_4_layers.xlsx'

all_sbatch_commands = []

server_experiment_folder = os.path.join(server_base_folder, f'attempt_1_32_seq_library')
server_design_folder = os.path.join(server_base_folder)
server_toml_file = os.path.join(server_experiment_folder, 'evolution_config.toml')
output_folder = batch_file_folder

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

with open(os.path.join(batch_file_folder, 'slurm_queue_gen_1.sh'), 'w') as f:  # writes batch file out for use
    for line in all_sbatch_commands:
        f.write(line)

