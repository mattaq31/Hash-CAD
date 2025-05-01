from .handle_evolution import EvolveManager
import importlib
from tqdm import tqdm
import numpy as np
import os

# To use this system you will need to install the optuna package (https://optuna.org) first.

optuna_spec = importlib.util.find_spec("optuna")  # only imports optuna if this is available
if optuna_spec is not None:
    import optuna

    optuna_available = True
else:
    optuna_available = False


class OptunaEvolveManager(EvolveManager):
    """
    An EvolveManager that is designed to be used with Optuna for optimizing the best hyperparameters.
    Inherits all other methods from the typical evolution manager.
    """
    def __init__(self, optuna_trial, **kwargs):
        if not optuna_available:
            raise ImportError('Optuna is not available on this system - the Optuna evolve manager cannot be used.')
        self.optuna_trial = optuna_trial
        super().__init__(**kwargs)

    def run_full_experiment(self, logging_interval=10):
        """
        Runs a full evolution experiment.
        :param logging_interval: The frequency at which logs should be written to file (including the best hamming array file).
        """
        if self.log_tracking_directory is None:
            raise ValueError('Log tracking directory must be specified to run an automatic full experiment.')
        with tqdm(total=self.max_evolution_generations - self.current_generation, desc='Evolution Progress', miniters=self.progress_bar_update_iterations) as pbar:
            for index, generation in enumerate(range(self.current_generation, self.max_evolution_generations)):

                self.single_evolution_step()
                self.optuna_trial.report(self.metrics['Best (Log) Physics-Based Score'][-1], generation)

                if index % logging_interval == 0:
                    self.export_results()

                pbar.update(1)
                pbar.set_postfix({f'Latest hamming score': self.metrics['Corresponding Hamming Distance'][-1],
                                  'Time for hamming calculation': self.metrics['Hamming Compute Time'][-1],
                                  'Latest log physics partition score': self.metrics['Best (Log) Physics-Based Score'][-1]}, refresh=False)

                if self.early_hamming_stop and max(self.metrics['Corresponding Hamming Distance']) >= self.early_hamming_stop:
                    break

                # Optuna can 'prune' i.e. stop a trial early if it thinks the trajectory is already very slow
                if self.optuna_trial.should_prune():
                    with open(os.path.join(self.log_tracking_directory, 'trial_pruned.txt'), 'w') as f:
                        f.write(f'Trial was pruned at generation {generation}')
                    raise optuna.TrialPruned()




