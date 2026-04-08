from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.slurm_process_and_run import create_o2_slurm_file
import os
import toml

slurm_parameters = {
    'num_cpus': 20,
    'memory': 16,
    'time_length': 24,
}

basic_evolution_parameters = {
    'early_max_valency_stop': 1,
    'evolution_generations': 2000,
    'evolution_population': 50,
    'process_count': 16,
    'generational_survivors': 3,
    'mutation_rate': 2,
    'unique_handle_sequences': 64,
    'split_sequence_handles': False,
    'mutation_type_probabilities': [0.425, 0.425, 0.15],
    'progress_bar_update_iterations': 10,
    'similarity_score_calculation_frequency': 10,
    'random_seed': 8,
    'suppress_handle_array_export': False,
    'save_first': True,
    'logging_interval': 100,
    'mutation_memory_system': 'off',
}

unique_handle_sequences = [8, 16, 32, 48, 64]
designs = ['sunflower', 'square']
all_sbatch_commands = []
server_slurm_folder = '/home/maa2818/hash_cad_paper_experiments/library_size_sweep/slurm_files'
local_output_folder = '/Users/matt/Desktop/library_size_sweep'
local_slurm_folder = os.path.join(local_output_folder, 'slurm_files')
create_dir_if_empty(local_output_folder, local_slurm_folder)

for design in designs:
    slat_array = f"/home/maa2818/hash_cad_paper_experiments/designs/basic_{design}.xlsx"
    design_directory = f"/home/maa2818/hash_cad_paper_experiments/library_size_sweep/{design}"
    create_dir_if_empty(os.path.join(local_output_folder, design))

    for handle_count in unique_handle_sequences:
        exp_name = f'handles_{handle_count}'
        local_experiment_folder = os.path.join(local_output_folder, design, exp_name)
        server_experiment_folder = os.path.join(design_directory, exp_name)
        evolution_config_file = os.path.join(server_experiment_folder, 'evolution_config.toml')
        create_dir_if_empty(local_experiment_folder)

        evolution_parameters = basic_evolution_parameters.copy()
        evolution_parameters['log_tracking_directory'] = server_experiment_folder
        evolution_parameters['slat_array'] = slat_array
        evolution_parameters['unique_handle_sequences'] = handle_count

        with open(os.path.join(local_experiment_folder, 'evolution_config.toml'), "w") as f:
            toml.dump(evolution_parameters, f)
        try:
            toml.load(os.path.join(local_experiment_folder, 'evolution_config.toml'))
        except:
            print(f'Error saving toml file for {design} {exp_name}')

        slurm_batch = create_o2_slurm_file(**slurm_parameters, command=f'handle_evolve -c {evolution_config_file}')
        slurm_file = os.path.join(local_slurm_folder, f'{design}_{exp_name}_call.sh')
        server_slurm_file = os.path.join(server_slurm_folder, f'{design}_{exp_name}_call.sh')

        with open(slurm_file, 'w') as f:
            for line in slurm_batch:
                f.write(line)

        all_sbatch_commands.append(f'sbatch {server_slurm_file}\n')

with open(os.path.join(local_output_folder, 'slurm_queue.sh'), 'w') as f:
    for line in all_sbatch_commands:
        f.write(line)
