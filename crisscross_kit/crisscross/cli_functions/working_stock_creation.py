import rich_click as click
import sys


@click.command(help='Automatically partitions an input IDT master stock plate into multiple working stock plates '
                    'at the selected concentration/volume.  Will also generate commands for the Echo to help facilitate the process.')
@click.option('--spec_sheet', '-s', default=None,
              help='Input IDT plate spec sheet', type=str)
@click.option('--output_directory', '-o', default='.',
              help='Output save directory.', type=str)
@click.option('--target_concentration', '-tc', required=True, type=int,
              help='General target concentration for all plates.')
@click.option('--target_volume', '-tv', required=True, type=int,
              help='General target volume for all plates.')
def create_working_stock_echo_sheet(spec_sheet, target_concentration, target_volume, output_directory):
    import pandas as pd
    from crisscross.helper_functions.simple_plate_visuals import visualize_plate_with_color_labels
    from plate_mapping import sanitize_plate_map
    from math import floor
    import os
    import numpy as np

    spec_df = pd.read_excel(spec_sheet, sheet_name=None, engine='calamine')['Plate Specs']
    # get all unique names in the 'Plate Name' column
    plate_names = spec_df['Plate Name'].unique()

    # run through all available plates
    for plate_name in plate_names:

        # standard data extraction
        selected_plate_df = spec_df[spec_df['Plate Name'] == plate_name]
        concentration_values = selected_plate_df['Measured Concentration µM '].values
        plate_wells = selected_plate_df['Well Position'].values
        max_volume_per_well = selected_plate_df['Final Volume µL '].values
        names = selected_plate_df['Sequence Name'].values

        # calculates how much master stock needs to be extracted to a working plate to achieve the target concentration/volume selected
        working_stock_volume = (target_concentration * target_volume) / concentration_values

        # calculates how many working plates can be created from multiples of the working stock volume
        working_plate_count = np.min(max_volume_per_well // working_stock_volume)

        # this is the remaining volume in each well after extraction for working plates
        remainder_vol = max_volume_per_well - (working_plate_count * working_stock_volume)

        # this is the buffer volume to add to the original master stock to achieve the working stock concentration again
        remainder_top_up_volume = (remainder_vol * (concentration_values/target_concentration)) - remainder_vol

        if any(working_stock_volume > max_volume_per_well):
            raise RuntimeError(f'For plate {plate_name}, one or more wells require a volume greater than the maximum final volume to achieve the target concentration and volume.')

        # combining all information into a visual plate map
        visual_dict = {}
        numeric_dict = {}
        numeric_topup_dict = {}
        for well_index, vol in enumerate(working_stock_volume):
            well_name = plate_wells[well_index]
            if well_name[1] == '0': # formatting to remove 0 in A01 for example
                well_name = well_name[0] + well_name[2]
            visual_dict[well_name] = '#40E0D0'

            # rounding to remove difficult numbers for pipetting
            numeric_dict[well_name] = round(vol, 0)
            numeric_topup_dict[well_name] = floor(remainder_top_up_volume[well_index]* 10) / 10

        visualize_plate_with_color_labels('384', visual_dict,
                                          direct_show=False,
                                          well_label_dict=numeric_dict,
                                          plate_title=f'{plate_name} (numbers = μl of master stock to add to achieve a working concentration of {target_concentration}μM in a total volume of {target_volume}μl).  You should create {int(working_plate_count)} working stock plates from the master plate.',
                                          save_file=f'{plate_name}_working_stock_map', save_folder=output_directory)
        visualize_plate_with_color_labels('384', visual_dict,
                                          direct_show=False,
                                          well_label_dict=numeric_topup_dict,
                                          plate_title=f'{plate_name} (numbers = μl of 1xTEF to add to master stock to achieve a working concentration of {target_concentration}μM in the original plate (post {int(working_plate_count)} working stock extractions))',
                                          save_file=f'{plate_name}_final_master_stock_refill_map', save_folder=output_directory)
        output_command_list = []
        dest_plate = sanitize_plate_map(plate_name) + '_working_stock'
        source_plate = sanitize_plate_map(plate_name)

        for well, vol, name in zip(plate_wells, working_stock_volume, names):
            output_command_list.append([name, source_plate, well, well, int(round(vol, 0)*1000), dest_plate, '384PP_AQ_BP'])  # convert to nl

        combined_df = pd.DataFrame(output_command_list, columns=['Component', 'Source Plate Name', 'Source Well',
                                                                 'Destination Well', 'Transfer Volume',
                                                                 'Destination Plate Name', 'Source Plate Type'])

        combined_df.to_csv(os.path.join(output_directory, f'{dest_plate}_echo_commands.csv'), index=False)

if __name__ == '__main__':
    create_working_stock_echo_sheet(sys.argv[1:])  # for use when debugging with pycharm

# volume left - need to get a concenrtation of 400uM
