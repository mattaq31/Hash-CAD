import rich_click as click
import sys

@click.command(help='This function accepts a .toml config file and will run the handle evolution process for the'
                    ' specified slat array and parameters (all within the config file).')
@click.option('--config_file', '-c', default=None,
              help='[String] Name or path of the evolution config file to be read in.')
def handle_evolve(config_file):
    from crisscross.assembly_handle_optimization.handle_evolution import EvolveManager
    import toml
    import pandas as pd
    import numpy as np

    evolution_params = toml.load(config_file)

    # reads in design here
    design_df = pd.read_excel(evolution_params['slat_array'], sheet_name=None, header=None)

    total_layers = 0
    for i, key in enumerate(design_df.keys()):
        if 'slat_layer_' in key:
            total_layers += 1

    slat_array = np.zeros((design_df['slat_layer_1'].shape[0], design_df['slat_layer_1'].shape[1], total_layers))

    handle_array_available = any('handle' in string for string in list(design_df.keys()))

    if handle_array_available:
        handle_array = np.zeros(
            (design_df['slat_layer_1'].shape[0], design_df['slat_layer_1'].shape[1], total_layers - 1))
    else:
        handle_array = None
    for i in range(total_layers):
        slat_array[..., i] = design_df['slat_layer_%s' % (i + 1)].values
        if i != total_layers - 1 and handle_array_available:
            handle_array[..., i] = design_df['handle_interface_%s' % (i + 1)].values

    slat_array[slat_array == -1] = 0 # knocks out any seed positions

    evolution_params['slat_array'] = slat_array

    if 'logging_interval' in evolution_params:
        logging_interval = evolution_params['logging_interval']
        del evolution_params['logging_interval']
    else:
        logging_interval = 10

    if np.sum(handle_array) == 0:
        handle_array = None

    evolve_manager = EvolveManager(**evolution_params, seed_handle_array=handle_array)

    evolve_manager.run_full_experiment(logging_interval)


if __name__ == '__main__':
    handle_evolve(sys.argv[1:])  # for use when debugging with pycharm
