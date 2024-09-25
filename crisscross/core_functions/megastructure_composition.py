import pandas as pd
import os
from colorama import Fore
from crisscross.helper_functions.plate_constants import plate96, plate384, plate96_center_pattern
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Patch
from string import ascii_uppercase
from collections import Counter

plt.rcParams.update({'font.sans-serif': 'Helvetica'})  # consistent figure formatting


def visualize_output_plates(output_well_descriptor_dict, plate_size, save_folder, save_file,
                            slat_display_format='pie', plate_display_aspect_ratio=1.495):
    """
    Prepares a visualization of the output plates for the user to be able to verify the design
    (or print out and use in the lab).
    :param output_well_descriptor_dict: Dictionary where key = (plate_number, well), and the value is a list with:
    [slat_name, [category counts [control, assembly, seed, cargo, undefined]
    for all 32 handles on H2 side e.g. 0 10 22 0 0], [same for H5 side]]
    :param plate_size: Either 96 or 384
    :param save_folder: Output folder
    :param save_file: Output filename
    :param plate_display_aspect_ratio: Aspect ratio to use for figure display - default matches true plate dimensions
    :param slat_display_format: Set to 'pie' to output an occupancy pie chart for each well,
    or 'barcode' to output a barcode showing the category of each individual handle
    :return: N/A
    """

    # prepares the graphical elements of the two plate types
    if plate_size == '96':
        row_divider = 12
        total_row_letters = 8
        plate = plate96
    elif plate_size == '384':
        row_divider = 24
        total_row_letters = 16
        plate = plate384
    else:
        raise RuntimeError('Plate size can only be 96 or 384.')

    standard_colors = ['k', 'r', 'g', 'b', 'm']

    # identifies how many plates need to be printed
    unique_plates = set()
    for key in output_well_descriptor_dict:
        unique_plates.add(key[0])

    for plate_number in unique_plates:
        fig, ax = plt.subplots(figsize=(total_row_letters * plate_display_aspect_ratio, total_row_letters))

        # Draws the rectangular box for the plate border
        rect = Rectangle((0, 0),
                         total_row_letters * plate_display_aspect_ratio,
                         total_row_letters,
                         linewidth=0.5, edgecolor='black', facecolor='none')
        ax.add_patch(rect)

        for well_index, well in enumerate(plate):
            x = well_index % row_divider + 0.5  # the 0.5 is there to make things easier to view
            y = well_index // row_divider + 0.5
            if (plate_number, well) in output_well_descriptor_dict:

                # the dictionary should contain the different components for both the H2 and H5 sides of the slat.
                # Both H2 and H5 should have a total sum of 32.  This means that the two sides of the pie chart should be equal.
                # black = control staples, red = assembly, green = seed, blue = cargo
                pool_details = output_well_descriptor_dict[(plate_number, well)]
                if slat_display_format == 'pie':
                    type_counts_h2 = Counter(pool_details[1])
                    type_counts_h5 = Counter(pool_details[2])
                    type_counts_h2 = [type_counts_h2[i] for i in range(5)]
                    type_counts_h5 = [type_counts_h5[i] for i in range(5)]

                    ax.pie(type_counts_h2 + type_counts_h5, center=(x, y),
                           colors=['k', 'r', 'g', 'b', 'm'], radius=0.3)
                    ax.plot([x - 0.3, x + 0.3], [y, y], linewidth=1.0, c='y')  # just a dividing line to make two side distinction more obvious
                elif slat_display_format == 'barcode':
                    for pool_ind, pool in enumerate(pool_details[::-1][:2]):
                        for handle_ind, handle in enumerate(pool):
                            square = Rectangle((x-0.3+(handle_ind*0.01875), y-((1-pool_ind)*0.3)),
                                               0.01875,
                                               0.3,
                                               linewidth=0.001,
                                               edgecolor=standard_colors[handle],
                                               facecolor=standard_colors[handle])
                            ax.add_patch(square)
                else:
                    raise RuntimeError('Invalid slat_display_format provided.')

                # adds identifying text details - offsets are hard-coded but seem to work for both 96 and 384 well plates
                ax.text(x, y - 0.39, pool_details[0], ha='center', va='center', fontsize=8)
                ax.text(x - 0.4, y + 0.2, 'H2', ha='center', va='center', fontsize=6)
                ax.text(x - 0.4, y - 0.2, 'H5', ha='center', va='center', fontsize=6)
            else:
                # empty well
                if slat_display_format == 'pie':
                    circle = Circle((x, y), radius=0.3, fill=None)
                    ax.add_patch(circle)
                elif slat_display_format == 'barcode':
                    square = Rectangle((x - 0.3, y - 0.3),
                                       0.6,
                                       0.6,
                                       fill=False,
                                       edgecolor='k')
                    ax.add_patch(square)

        # Set the y-axis labels to the plate letters
        ax.set_yticks([i + 0.5 for i in range(total_row_letters)])
        ax.set_yticklabels(ascii_uppercase[:total_row_letters], fontsize=18)
        ax.yaxis.set_tick_params(pad=15)
        ax.tick_params(axis='y', which='both', length=0)

        # Set the x-axis labels to the plate numbers
        ax.set_xticks([i + 0.5 for i in range(row_divider)])
        ax.set_xticklabels([i + 1 for i in range(row_divider)], fontsize=18)
        ax.tick_params(axis='x', which='both', length=0)
        ax.xaxis.tick_top()

        if len(output_well_descriptor_dict) > 0:
            # legend creation
            labels = ['Control Handles', 'Assembly Handles', 'Seed Handles', 'Cargo Handles', 'Undefined']
            wedges = [Patch(color=color, label=label) for color, label in zip(standard_colors, labels)]
            ax.legend(wedges, labels,
                      loc='upper center',
                      bbox_to_anchor=(0.5, 0.0), ncol=5,
                      fancybox=True, fontsize=14)
        else:
            print(Fore.RED + f'Seems like plate {plate_number} has no operations assigned to it.' + Fore.RESET)

        # sets limits according to number of rows/cols.  Y-axis is inverted to make it easier for compatibilty with different plate types
        ax.set_xlim(0, row_divider)
        ax.set_ylim(total_row_letters, -0.1)
        plt.tight_layout()
        plt.savefig(os.path.join(save_folder, f'{save_file}-viz-plate-{plate_number}.pdf'))
        plt.close()


def convert_slats_into_echo_commands(slat_dict, destination_plate_name, output_folder, output_filename,
                                     default_transfer_volume=75, source_plate_type='384PP_AQ_BP',
                                     output_empty_wells=False,
                                     manual_plate_well_assignments=None, unique_transfer_volume_for_plates=None,
                                     output_plate_size='96', center_only_well_pattern=False,
                                     generate_plate_visualization=True, plate_viz_type='barcode'):
    """
    Converts a dictionary of slats into an echo liquid handler command list for all handles provided.
    :param slat_dict: Dictionary of slat objects
    :param destination_plate_name: The name of the design's destination output plate
    :param output_folder: The output folder to save the file to
    :param output_filename: The name of the output file
    :param default_transfer_volume: The transfer volume for each handle (either a single integer, or a list of integers for each individual slat)
    :param source_plate_type: The physical plate type in use
    :param output_empty_wells: Outputs an empty row for a well if a handle is only a placeholder
    :param manual_plate_well_assignments: The specific output wells to use for each slat (if not provided, the script will automatically assign wells).
    This can be either a list of tuples (plate number, well name) or a dictionary of tuples.
    :param unique_transfer_volume_for_plates: Dictionary assigning a special transfer volume for certain plates (supersedes all other settings)
    :param output_plate_size: Either '96' or '384' for the output plate size
    :param center_only_well_pattern: Set to true to force output wells to be in the center of the plate.  This is only available for 96-well plates.
    :param generate_plate_visualization: Set to true to generate a graphic showing the postions and contents of each well in the output plates
    :param plate_viz_type: Set to 'barcode' to show a barcode of the handle types in each well, or 'pie' to show a pie chart of the handle types
    :return: Pandas dataframe corresponding to output ech handler command list
    """

    # echo command prep
    output_command_list = []
    output_well_list = []
    output_plate_num_list = []
    output_well_descriptor_dict = {}

    if output_plate_size == '96':
        plate_format = plate96
        if center_only_well_pattern:  # wells only in the center of the plate to make it easier to add lids
            plate_format = plate96_center_pattern
    elif output_plate_size == '384':
        plate_format = plate384
        if center_only_well_pattern:
            raise NotImplementedError('Center only well pattern is not available for 384 well output plates.')
    else:
        raise ValueError('Invalid plate size provided')

    # prepares the exact output wells and plates for the slat dictionary provided
    if manual_plate_well_assignments is None:
        if len(slat_dict) > len(plate_format):
            print(Fore.BLUE + 'Too many slats for one plate, splitting into multiple plates.')
        for index, (_, slat) in enumerate(slat_dict.items()):
            if index // len(plate_format) > 0:
                well = plate_format[index % len(plate_format)]
                plate_num = index // len(plate_format) + 1
            else:
                well = plate_format[index]
                plate_num = 1

            output_well_list.append(well)
            output_plate_num_list.append(plate_num)
    else:
        if len(manual_plate_well_assignments) != len(slat_dict):
            raise ValueError('The well count provided does not match the number of slats in the output dictionary.')
        for index, (slat_name, slat) in enumerate(slat_dict.items()):
            if isinstance(manual_plate_well_assignments, dict):
                plate_num, well = manual_plate_well_assignments[slat_name]
            elif isinstance(manual_plate_well_assignments, list):
                plate_num, well = manual_plate_well_assignments[index]
            else:
                raise ValueError('Invalid manual_plate_well_assignments format provided (needs to be a list or dict).')
            output_well_list.append(well)
            output_plate_num_list.append(plate_num)

    # runs through all the handles for each slats and outputs the plate and well for both the input and output
    for index, (slat_name, slat) in enumerate(slat_dict.items()):
        slat_h2_data = slat.get_sorted_handles('h2')
        slat_h5_data = slat.get_sorted_handles('h5')
        for (handle_num, handle_data), handle_side in zip(slat_h2_data + slat_h5_data,
                                                          ['h2'] * len(slat_h2_data) + ['h5'] * len(slat_h2_data)):
            if 'plate' not in handle_data:
                if output_empty_wells:  # this is the case where a placeholder handle is used (no plate available).
                    #  If the user indicates they want to manually add in these handles,
                    #  this will output placeholders for the specific wells that need manual handling.
                    output_command_list.append([slat_name + '_%s_staple_%s' % (handle_side, handle_num),
                                                'MANUAL TRANSFER', 'MANUAL TRANSFER',
                                                output_well_list[index], default_transfer_volume,
                                                f'{destination_plate_name}_{output_plate_num_list[index]}',
                                                'MANUAL TRANSFER'])
                    continue
                else:
                    raise RuntimeError(f'The design provided has an incomplete slat: {slat_name} (slat ID {slat.ID})')

            # certain plates will need different input volumes if they have different handle concentrations
            if unique_transfer_volume_for_plates is not None and handle_data[
                'plate'] in unique_transfer_volume_for_plates:
                handle_specific_vol = unique_transfer_volume_for_plates[handle_data['plate']]
            else:
                handle_specific_vol = default_transfer_volume

            if ',' in slat_name:
                raise RuntimeError('Slat names cannot contain commas - this will cause issues with the echo csv  file.')
            output_command_list.append([slat_name + '_%s_staple_%s' % (handle_side, handle_num),
                                        handle_data['plate'], handle_data['well'],
                                        output_well_list[index], handle_specific_vol,
                                        f'{destination_plate_name}_{output_plate_num_list[index]}',
                                        source_plate_type])

        # tracking command for visualization purposes
        all_handle_types = []
        for slat_data in [slat_h2_data, slat_h5_data]:
            handle_types = []
            for handle in slat_data:
                if 'descriptor' not in handle[1]:  # no description provided i.e. undefined
                    handle_types += [4]
                else:
                    if 'Cargo' in handle[1]['descriptor']:
                        handle_types += [3]
                    elif 'Assembly' in handle[1]['descriptor'] or 'Ass.' in handle[1]['descriptor']:
                        handle_types += [1]
                    elif 'Seed' in handle[1]['descriptor']:
                        handle_types += [2]
                    else:  # control handles
                        handle_types += [0]
            all_handle_types.append(handle_types)
        output_well_descriptor_dict[(output_plate_num_list[index], output_well_list[index])] = [
                                                                                                   slat_name] + all_handle_types

    combined_df = pd.DataFrame(output_command_list, columns=['Component', 'Source Plate Name', 'Source Well',
                                                             'Destination Well', 'Transfer Volume',
                                                             'Destination Plate Name', 'Source Plate Type'])

    combined_df.to_csv(os.path.join(output_folder, output_filename), index=False)

    if generate_plate_visualization:
        visualize_output_plates(output_well_descriptor_dict, output_plate_size, output_folder,
                                output_filename.split('.')[0],
                                slat_display_format='barcode')  # prepares a visualization of the output plates

    return combined_df
