import os
import toml

experiment_folder = '/home/maa2818/hamming_optimization_experiments/experiment_folders/optuna_hyperparam_v1'


def optuna_optim(trial):
    trial_folder = os.path.join(experiment_folder, f'trial_{trial.number}')
    if not os.path.exists(trial_folder):
        os.makedirs(trial_folder)

    handle_antihandle_probability = trial.suggest_float("mutation_type_probabilities_1", 0.0, 0.5)
    mutation_probabilities = [handle_antihandle_probability, handle_antihandle_probability,
                              1 - (2 * handle_antihandle_probability)]
    evolution_population = trial.suggest_int("evolution_population", 30, 1000)
    generational_survivors = trial.suggest_int("generational_survivors", 2, 20)
    mutation_rate = trial.suggest_float("mut_rate", 0.001, 0.4)

    evolution_params = {
        'handle_antihandle_probability': handle_antihandle_probability,
        'evolution_population': evolution_population,
        'generational_survivors': generational_survivors,
        'mutation_probabilities': mutation_probabilities,
        'mutation_rate': mutation_rate,
    }

    with open(os.path.join(trial_folder, 'evolution_config.toml'), "w") as f:
        toml.dump(evolution_params, f)

    evolve_manager = OptunaEvolveManager(slat_array, unique_handle_sequences=32,
                                         early_hamming_stop=31, evolution_population=evolution_population,
                                         generational_survivors=generational_survivors,
                                         mutation_rate=mutation_rate,
                                         process_count=18,
                                         evolution_generations=1000,
                                         mutation_type_probabilities=mutation_probabilities,
                                         split_sequence_handles=False,
                                         progress_bar_update_iterations=5,
                                         log_tracking_directory=trial_folder, optuna_trial=trial)

    final_physics_score = multirule_oneshot_hamming(slat_array,
                                                    evolve_manager.handle_array,
                                                    per_layer_check=False,
                                                    report_worst_slat_combinations=False,
                                                    request_substitute_risk_score=False)[
        'Physics-Informed Partition Score']
    return final_physics_score


if __name__ == '__main__':
    from crisscross.assembly_handle_optimization import generate_random_slat_handles
    from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming
    from crisscross.assembly_handle_optimization.handle_evolve_with_optuna import OptunaEvolveManager
    from crisscross.core_functions.slat_design import generate_standard_square_slats
    import optuna
    import pickle

    slat_array, unique_slats_per_layer = generate_standard_square_slats(32)  # standard square
    handle_array = generate_random_slat_handles(slat_array, 32)

    study = optuna.create_study(directions=["maximize"])

    for i in range(100):
        study.optimize(optuna_optim, n_trials=10, gc_after_trial=True)
        with open(os.path.join(experiment_folder, f'study_trial_{(i * 10) + 10}.pkl'), 'wb') as f:
            pickle.dump(study, f)
