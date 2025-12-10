import os
import toml
import pandas as pd
from crisscross.helper_functions.slurm_process_and_run import create_o2_slurm_file

target_directory = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Papers/hash_cad/evolution_runs/parameter_sweep'
designs = ['hexagon', 'sunflower']
all_sbatch_commands = []

slurm_parameters = {
    'num_cpus': 20,
    'memory': 16,
    'time_length': 48,
}
server_slurm_folder = '/home/maa2818/hash_cad_paper_experiments/parameter_sweep/slurm_files'

for design in designs:
    design_directory = os.path.join(target_directory, design)
    server_design_directory = f"/home/maa2818/hash_cad_paper_experiments/parameter_sweep/{design}"
    skipped_tally = 0
    total_tally = 0

    for experiment in os.listdir(design_directory):
        # Skip non-directory files
        if not os.path.isdir(os.path.join(design_directory, experiment)):
            continue
        experiment_directory = os.path.join(design_directory, experiment)
        metrics_file = os.path.join(experiment_directory, 'metrics.csv')
        param_file = os.path.join(experiment_directory, 'evolution_config.toml')
        generations = toml.load(param_file)['evolution_generations']
        metrics_df = pd.read_csv(metrics_file)
        if len(metrics_df) < generations:
            print(f'Rerunning {design} {experiment}, only completed {len(metrics_df)}/{generations} generations')
            skipped_tally += 1

            server_experiment_folder = os.path.join(server_design_directory, experiment)
            evolution_config_file = os.path.join(server_experiment_folder, f'evolution_config.toml')
            slurm_batch = create_o2_slurm_file(**slurm_parameters, command=f'handle_evolve -c {evolution_config_file}')
            local_slurm_file = os.path.join(target_directory, 'slurm_files', f'{design}_{experiment}_call.sh')

            with open(local_slurm_file, 'w') as f:  # writes batch file out for use
                for line in slurm_batch:
                    f.write(line)

            server_slurm_file = os.path.join(server_slurm_folder, f'{design}_{experiment}_call.sh')
            all_sbatch_commands.append(f'sbatch {server_slurm_file}\n')

        total_tally += 1
    print(f'{design}: {skipped_tally}/{total_tally} experiments need to be rerun')
    print('-----')
with open(os.path.join(target_directory, 'slurm_queue_reruns.sh'), 'w') as f:  # writes batch file out for use
    for line in all_sbatch_commands:
        f.write(line)
