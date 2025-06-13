import rich_click as click
import sys

@click.command(help='This function accepts a .toml config file and will run the handle evolution process for the'
                    ' specified slat array and parameters (all within the config file).')
@click.option('--config_file', '-c', default=None,
              help='[String] Name or path of the evolution config file to be read in.')
def handle_evolve(config_file):
    from crisscross.assembly_handle_optimization.handle_evolution import EvolveManager
    from crisscross.core_functions.megastructures import Megastructure
    import toml
    import numpy as np

    evolution_params = toml.load(config_file)

    megastructure = Megastructure(import_design_file=evolution_params['slat_array'])

    slat_array = megastructure.generate_slat_occupancy_grid()
    evolution_params['slat_array'] = slat_array

    handle_array = megastructure.generate_assembly_handle_grid()
    if np.sum(handle_array) == 0:
        handle_array = None

    if 'logging_interval' in evolution_params:
        logging_interval = evolution_params['logging_interval']
        del evolution_params['logging_interval']
    else:
        logging_interval = 10

    evolve_manager = EvolveManager(**evolution_params, seed_handle_array=handle_array)

    evolve_manager.run_full_experiment(logging_interval)


if __name__ == '__main__':
    handle_evolve(sys.argv[1:])  # for use when debugging with pycharm
