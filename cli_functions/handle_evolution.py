
import rich_click as click


@click.command(help='This function accepts a .toml config file and will run the handle evolution process for the'
                    ' specified slat array and parameters (all within the config file).')
@click.option('--config_file', '-c', default=None,
              help='[String] Name or path of the evolution config file to be read in.')
def handle_evolve(config_file):
    from crisscross.assembly_handle_optimization.handle_evolution import evolve_handles_from_slat_array
    import toml
    import pandas as pd
    import numpy as np

    evolution_params = toml.load(config_file)

    # reads in design here
    design_df = pd.read_excel(evolution_params['slat_array'], sheet_name=None, header=None)
    slat_array = np.zeros((design_df['slat_layer_1'].shape[0], design_df['slat_layer_1'].shape[1], len(design_df)))
    for i, key in enumerate(design_df.keys()):
        slat_array[..., i] = design_df[key].values

    slat_array[slat_array == -1] = 0 # knocks out any seed positions

    evolution_params['slat_array'] = slat_array

    evolve_handles_from_slat_array(**evolution_params)
