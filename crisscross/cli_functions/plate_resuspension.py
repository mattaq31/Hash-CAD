import rich_click as click
import sys

@click.command(help='This command generates resuspension maps for all provided DNA spec files, which makes it easy '
                    'to interface directly with a liquid handler such as an EpMotion.')
@click.option('--input_directory', '-i', default=None,
              help='Input directory to extract spec sheets.', type=str)
@click.option('--input_files', '-if', multiple=True, default=None,
              help='Specific excel sheets to analyze (can provide multiple)', type=str)
@click.option('--output_directory', '-o', default='.',
              help='Output save directory.', type=str)
@click.option('--target_concentration', '-tc', default=1000,
              help='General target concentration for all plates.')
@click.option('--volume_cap_ul', '-vc', default=120,
              help='Maximum well resuspension volume.')
@click.option('--target_concentration_per_plate', '-t', multiple=True, default=None,
              help='Specific target concentration for specific plates (can provide multiple)', type=(str, int))
@click.option('--max_commands_per_file', '-mc', default=None, type=int,
              help='Max commands to include in each liquid handler csv file.')
@click.option('--plot_distributions_per_plate', '-p', is_flag=True,
              help='Set this flag to plot the distribution of volumes generated per plates.')
@click.option('--plate_size', type=str, default='384',
              help='Sets the size of the plate to be used for resuspension.')
def plate_resuspension(input_directory, input_files, output_directory, target_concentration, volume_cap_ul,
                       target_concentration_per_plate, max_commands_per_file, plot_distributions_per_plate, plate_size):
    from crisscross.helper_functions.lab_helper_sheet_generation import prepare_liquid_handle_plates_multiple_files


    if target_concentration_per_plate:
        temp_dict = {}
        for plate_name, target_conc in target_concentration_per_plate:
            temp_dict[plate_name] = target_conc
        target_concentration_per_plate = temp_dict

    prepare_liquid_handle_plates_multiple_files(output_directory, file_list=input_files, extract_all_from_folder=input_directory,
                                                target_concentration_uM=target_concentration,
                                                volume_cap_ul=volume_cap_ul,
                                                target_concentration_per_plate=target_concentration_per_plate,
                                                max_commands_per_file=max_commands_per_file,
                                                plot_distribution_per_plate=plot_distributions_per_plate, plate_size=plate_size)

if __name__ == '__main__':
    plate_resuspension(sys.argv[1:])  # for use when debugging with pycharm
