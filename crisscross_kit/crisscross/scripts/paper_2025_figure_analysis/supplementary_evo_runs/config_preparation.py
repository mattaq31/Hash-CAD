from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.slurm_process_and_run import create_o2_slurm_file
import os
import toml

slurm_parameters = {
    'num_cpus': 20,
    'memory': 16,
    'time_length': 12,
}

basic_evolution_parameters = {
    'early_max_valency_stop': 31,
    'evolution_generations': 10000,
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
    'suppress_handle_array_export': True,
    'logging_interval': 1,
    'mutation_memory_system': 'off',
}

customized_population = [5, 50, 250, 500, 1000]
customized_survivors = [1, 3, 5, 10]
customized_mutation_rates = [1, 2, 3, 5, 7, 10]
customized_probabilities = [
    [0, 0, 1],
    [0.5, 0.5, 0],
    [0.425, 0.425, 0.15],
    [0.075, 0.075, 0.85]
]

designs = ['hexagon', 'sunflower']
all_sbatch_commands = []
server_slurm_folder = '/home/maa2818/hash_cad_paper_experiments/parameter_sweep/slurm_files'
local_output_folder = '/Users/matt/Desktop/parameter_sweep'
local_slurm_folder = os.path.join(local_output_folder, 'slurm_files')
create_dir_if_empty(local_output_folder, local_slurm_folder)

for design in designs:
    slat_array = f"/home/maa2818/hash_cad_paper_experiments/designs/basic_{design}.xlsx"
    design_directory = f"/home/maa2818/hash_cad_paper_experiments/parameter_sweep/{design}"
    create_dir_if_empty(os.path.join(local_output_folder, design))

    for population in customized_population:
        for survivors in customized_survivors:
            for mut_rate in customized_mutation_rates:
                for mut_probs in customized_probabilities:
                    if survivors > population: # impossible to run with this config
                        continue
                    exp_name = f'pop_{population}_surv_{survivors}_mut_{mut_rate}_probs_{"-".join([str(int(p*100)) for p in mut_probs])}'
                    local_experiment_folder = os.path.join(local_output_folder, design, exp_name)
                    server_experiment_folder = os.path.join(design_directory, exp_name)
                    evolution_config_file = os.path.join(server_experiment_folder, f'evolution_config.toml')
                    create_dir_if_empty(local_experiment_folder)

                    evolution_parameters = basic_evolution_parameters.copy()
                    evolution_parameters['log_tracking_directory'] = server_experiment_folder
                    evolution_parameters['slat_array'] = slat_array
                    evolution_parameters['evolution_population'] = population
                    evolution_parameters['generational_survivors'] = survivors
                    evolution_parameters['mutation_rate'] = mut_rate
                    evolution_parameters['mutation_type_probabilities'] = mut_probs
                    evolution_parameters['evolution_generations'] = int(evolution_parameters['evolution_generations'] * 50/population) # epoch count adjusted in relation to evolution population

                    with open(os.path.join(local_experiment_folder, f'evolution_config.toml'), "w") as f:
                        toml.dump(evolution_parameters, f)
                    slurm_batch = create_o2_slurm_file(**slurm_parameters, command=f'handle_evolve -c {evolution_config_file}')
                    slurm_file  = os.path.join(local_slurm_folder, f'{design}_{exp_name}_call.sh')
                    server_slurm_file = os.path.join(server_slurm_folder, f'{design}_{exp_name}_call.sh')

                    with open(slurm_file, 'w') as f:  # writes batch file out for use
                        for line in slurm_batch:
                            f.write(line)

                    all_sbatch_commands.append(f'sbatch {server_slurm_file}\n')

with open(os.path.join(local_output_folder, 'slurm_queue.sh'), 'w') as f:  # writes batch file out for use
    for line in all_sbatch_commands:
        f.write(line)
