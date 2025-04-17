from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.slurm_process_and_run import create_o2_slurm_file
import os
import toml

root_folder = f'/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/hash_cad_validation_designs'
design_folder = os.path.join(root_folder, 'designs')
batch_file_folder = os.path.join(root_folder, 'handle_evolution')
server_base_folder = '/home/maa2818/hash_cad_validation_designs'

create_dir_if_empty(design_folder, batch_file_folder)

slurm_parameters = {
    'num_cpus': 20,
    'memory': 16,
    'time_length': 24,
}

evolution_parameters = {
    'early_hamming_stop': 31,
    'evolution_generations': 20000,
    'evolution_population': 800,
    'process_count': 18,
    'generational_survivors': 5,
    'mutation_rate': 2,
    'slat_length': 32,
    'unique_handle_sequences': 32,
    'split_sequence_handles': True,
    'mutation_type_probabilities': [0.425, 0.425, 0.15],
    'progress_bar_update_iterations': 10,
    'random_seed': 8,
    'mutation_memory_system': 'off',
}

all_sbatch_commands = []

for batch_name, design in zip(['bird'], ['bird_design.xlsx']):
    for seq_count in [64]:
        for mut_rate in [2]:
            exp_name = f'{batch_name}_{seq_count}_seq_library_mut_{str(mut_rate).replace(".","-")}'
            server_experiment_folder = os.path.join(server_base_folder, batch_name, exp_name)
            server_design_folder = os.path.join(server_base_folder, 'designs')
            server_toml_file = os.path.join(server_experiment_folder, 'evolution_config.toml')
            output_folder = os.path.join(batch_file_folder, batch_name, exp_name)
            create_dir_if_empty(output_folder)

            evolution_parameters['log_tracking_directory'] = server_experiment_folder
            evolution_parameters['slat_array'] = os.path.join(server_design_folder, design)
            evolution_parameters['unique_handle_sequences'] = seq_count
            evolution_parameters['mutation_rate'] = mut_rate

            with open(os.path.join(output_folder, f'evolution_config.toml'), "w") as f:
                toml.dump(evolution_parameters, f)

            slurm_batch = create_o2_slurm_file(**slurm_parameters, command=f'handle_evolve -c {server_toml_file}')
            slurm_file  = os.path.join(output_folder, f'server_call.sh')
            server_slurm_file = os.path.join(server_experiment_folder, 'server_call.sh')

            with open(slurm_file, 'w') as f:  # writes batch file out for use
                for line in slurm_batch:
                    f.write(line)
            all_sbatch_commands.append(f'sbatch {server_slurm_file}\n')

with open(os.path.join(root_folder, 'slurm_queue.sh'), 'w') as f:  # writes batch file out for use
    for line in all_sbatch_commands:
        f.write(line)

