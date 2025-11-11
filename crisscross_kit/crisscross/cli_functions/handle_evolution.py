import rich_click as click
import sys

@click.command(help='This function accepts a .toml config file and will run the handle evolution process for the'
                    ' specified slat array and parameters (all within the config file).')
@click.option('--config_file', '-c', default=None,
              help='[String] Name or path of the evolution config file to be read in.')
def handle_evolve(config_file):
    from crisscross.slat_handle_match_evolver.handle_evolution import EvolveManager
    from crisscross.core_functions.megastructures import Megastructure
    import toml

    evolution_params = toml.load(config_file)

    megastructure = Megastructure(import_design_file=evolution_params['slat_array'])
    del evolution_params['slat_array']

    if 'logging_interval' in evolution_params:
        logging_interval = evolution_params['logging_interval']
        del evolution_params['logging_interval']
    else:
        logging_interval = 10

    if 'suppress_handle_array_export' in evolution_params:
        suppress_handle_array_export = evolution_params['suppress_handle_array_export']
        del evolution_params['suppress_handle_array_export']
    else:
        suppress_handle_array_export = False

    evolve_manager = EvolveManager(**evolution_params, megastructure=megastructure)

    evolve_manager.run_full_experiment(logging_interval, suppress_handle_array_export=suppress_handle_array_export)


if __name__ == '__main__':
    handle_evolve(sys.argv[1:])  # for use when debugging with pycharm
