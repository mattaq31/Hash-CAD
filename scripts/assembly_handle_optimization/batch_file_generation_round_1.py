from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.slurm_process_and_run import create_o2_slurm_file
import os
import toml

# will be testing 2 designs - square + glider
# will be testing handle library between 16-64 for square
# for glider, will be testing 32-64 for universal handles
# then will also be testing 32-64 for split handles (i.e. 16-32)

root_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/assembly_handle_optimization'
design_folder = os.path.join(root_folder, 'slat_designs')
batch_file_folder = os.path.join(root_folder, 'experiment_folders')
server_base_folder = '/home/maa2818/hamming_optimization_experiments'
create_dir_if_empty(design_folder, batch_file_folder)

slurm_parameters = {
    'num_cpus': 20,
    'memory': 16,
    'time_length': 11,
}

evolution_parameters = {
    'early_hamming_stop': 31,
    'evolution_generations': 2000,
    'evolution_population': 300,
    'process_count': 18,
    'generational_survivors': 5,
    'mutation_rate': 0.03,
    'slat_length': 32,
    'unique_handle_sequences': 32,
    'split_sequence_handles': False,
    'progress_bar_update_iterations': 10,
    'random_seed': 8,
}

design_1 = 'basic_square.xlsx'

for library_count in range(16, 64):
    server_experiment_folder = os.path.join(server_base_folder, f'experiment_folders/base_square_{library_count}_handle_library')
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

    with open(os.path.join(output_folder, 'server_call.sh'), 'w') as f:  # writes batch file out for use
        for line in slurm_batch:
            f.write(line)

