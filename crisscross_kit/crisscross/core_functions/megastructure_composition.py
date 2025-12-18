import pandas as pd
import os
from colorama import Fore, Style
from crisscross.helper_functions import plate96, plate384, plate96_center_pattern
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Patch
from string import ascii_uppercase
from collections import Counter
import platform
import math

# consistent figure formatting between mac, windows and linux
if platform.system() == 'Darwin':
    plt.rcParams.update({'font.sans-serif': 'Helvetica'})
elif platform.system() == 'Windows':
    plt.rcParams.update({'font.sans-serif': 'Arial'})
else:
    plt.rcParams.update({'font.sans-serif': 'DejaVu Sans'}) # should work with linux


def visualize_output_plates(output_well_descriptor_dict, plate_size, save_folder, save_file,
                            slat_display_format='pie', plate_display_aspect_ratio=1.495):
    """
    Prepares a visualization of the output plates for the user to be able to verify the design
    (or print out and use in the lab).
    :param output_well_descriptor_dict: Dictionary where key = (plate_number, well), and the value is a list with:
    [slat_name, [category for all 32 handles on H2 side e.g. 0 2 3 4 0], [same for H5 side], slat_color, slat_type], where the categories are:
    0 = control, 1 = assembly, 2 = seed, 3 = cargo, 4 = undefined
    :param plate_size: Either 96 or 384
    :param save_folder: Output folder
    :param save_file: Output filename
    :param plate_display_aspect_ratio: Aspect ratio to use for figure display - default matches true plate dimensions
    :param slat_display_format: Set to 'pie' to output an occupancy pie chart for each well,
    'barcode' to output a barcode showing the category of each individual handle, or
    'stacked_barcode' for a more detailed view
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
                           colors=['k', 'r', 'g', 'b', 'm'], radius=0.3) # pie radius 0.3 - occupies full view

                    ax.text(x - 0.4, y + 0.2, 'H2', ha='center', va='center', fontsize=6)
                    ax.text(x - 0.4, y - 0.2, 'H5', ha='center', va='center', fontsize=6)

                    # adds identifying slat name
                    ax.text(x, y - 0.39, pool_details[0], ha='center', va='center', fontsize=8)
                    # adds slat type identifier
                    ax.text(x, y + 0.3, pool_details[4] if pool_details[4] != 'tube' else 'standard', ha='center', va='center', fontsize=6)
                elif slat_display_format == 'barcode':
                    for pool_ind, pool in enumerate(pool_details[::-1][2:4]):
                        for handle_ind, handle in enumerate(pool):
                            # slat positions identified with barcode rectangles
                            # 0.3 = full width, 0.15 = half height, 0.01875 = 1/32 of width
                            square = Rectangle((x-0.3+(handle_ind*0.01875), y-((1-pool_ind)*0.15)),
                                               0.01875,
                                               0.15,
                                               linewidth=0.001,
                                               edgecolor=standard_colors[handle],
                                               facecolor=standard_colors[handle])
                            ax.add_patch(square)
                    # slightly tweaked text positioning for better visualization
                    ax.text(x - 0.4, y + 0.2, 'H2', ha='center', va='center', fontsize=6)
                    ax.text(x - 0.4, y - 0.2, 'H5', ha='center', va='center', fontsize=6)
                    ax.text(x - 0.35, y - 0.075, '1', ha='center', va='center', fontsize=4)
                    ax.text(x + 0.35, y - 0.075, '32', ha='center', va='center', fontsize=4)
                    # adds identifying slat name
                    ax.text(x, y - 0.37, pool_details[0], ha='center', va='center', fontsize=8)
                    # adds slat type identifier
                    ax.text(x, y + 0.3, pool_details[4] if pool_details[4] != 'tube' else 'standard', ha='center', va='center', fontsize=6)

                elif slat_display_format == 'stacked_barcode':
                    for pool_ind, pool in enumerate(pool_details[::-1][2:4]):
                        for handle_ind, handle in enumerate(pool):
                            x_offset = handle_ind % 16
                            y_offset = (handle_ind // 16) + (2*pool_ind)
                            # slat positions identified with barcode rectangles - 16 per row (4 rows total)
                            # 0.3 = full width, 0.1125 = half height, 0.0375 = 1/16 of width
                            square = Rectangle((x-0.3+(x_offset*0.0375), y-(0.225 - y_offset*0.1125)),
                                               0.0375,
                                               0.1125,
                                               linewidth=0.01,
                                               edgecolor='w', # to allow for easy counting of positions
                                               facecolor=standard_colors[handle])
                            ax.add_patch(square)
                    # customized annotations for this particular view
                    ax.text(x - 0.35, y - 0.16875, '1', ha='center', va='center', fontsize=4)
                    ax.text(x + 0.35, y - 0.16875, '16', ha='center', va='center', fontsize=4)
                    ax.text(x - 0.35, y - 0.05625, '17', ha='center', va='center', fontsize=4)
                    ax.text(x + 0.35, y - 0.05625, '32', ha='center', va='center', fontsize=4)
                    ax.text(x, y + 0.3, 'H2', ha='center', va='center', fontsize=6)
                    ax.text(x, y - 0.275, 'H5', ha='center', va='center', fontsize=6)
                    # adds identifying slat name
                    ax.text(x, y - 0.41, pool_details[0], ha='center', va='center', fontsize=8)
                    # adds slat type identifier
                    ax.text(x, y + 0.3, pool_details[4] if pool_details[4] != 'tube' else 'standard', ha='center', va='center', fontsize=6)

                else:
                    raise RuntimeError('Invalid slat_display_format provided.')

                # just a dividing line to make two side distinction more obvious
                ax.plot([x - 0.3, x + 0.3], [y, y], linewidth=1.0, c='y')

                # add a coloured boundary box around the well using the pool_details[3] (unique slat color)
                if pool_details[3] is not None:
                    square = Rectangle((x - 0.5, y - 0.5),
                                       1.0,
                                       0.9,
                                       linewidth=2.0,
                                       facecolor='none',
                                       edgecolor=pool_details[3])
                    ax.add_patch(square)
            else:
                # empty wells
                if slat_display_format == 'pie':
                    circle = Circle((x, y), radius=0.3, fill=None)
                    ax.add_patch(circle)
                elif slat_display_format == 'barcode':
                    square = Rectangle((x - 0.3, y - 0.15),
                                       0.6,
                                       0.3,
                                       facecolor='none',
                                       edgecolor='k')
                    ax.add_patch(square)
                elif slat_display_format == 'stacked_barcode':
                    square = Rectangle((x - 0.3, y - 0.225),
                                       0.6,
                                       0.45,
                                       facecolor='none',
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

        # deletes the axis spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)

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

        # sets limits according to number of rows/cols.  Y-axis is inverted to make it easier for compatibility with different plate types
        ax.set_xlim(0, row_divider)
        ax.set_ylim(total_row_letters, -0.1)
        plt.tight_layout()
        plt.savefig(os.path.join(save_folder, f'{save_file}-viz-plate-{plate_number}.pdf'))
        plt.close()


def convert_slats_into_echo_commands(slat_dict, destination_plate_name, output_folder, output_filename,
                                     reference_transfer_volume_nl=75, reference_concentration_uM=500,
                                     transfer_volume_multiplier_for_slats=None,
                                     source_plate_type='384PP_AQ_BP',
                                     output_empty_wells=False,
                                     manual_plate_well_assignments=None, unique_transfer_volume_for_plates=None,
                                     output_plate_size='96', center_only_well_pattern=False,
                                     generate_plate_visualization=True, plate_viz_type='stacked_barcode',
                                     destination_well_max_volume=25, normalize_volumes=False, color_output_wells=True):
    """
    Converts a dictionary of slats into an echo liquid handler command list for all handles provided.
    :param slat_dict: Dictionary of slat objects
    :param destination_plate_name: The name of the design's destination output plate
    :param output_folder: The output folder to save the file to
    :param output_filename: The name of the output file
    :param reference_transfer_volume_nl: The default transfer volume for each handle (in nL)
    :param reference_concentration_uM: The default concentration matching that of the selected transfer volume (in uM)
    :param transfer_volume_multiplier_for_slats: Dictionary assigning a special transfer multiplier for specified slats (will be applied to all special plate volumes too)
    :param source_plate_type: The physical plate type in use
    :param output_empty_wells: Outputs an empty row for a well if a handle is only a placeholder
    :param manual_plate_well_assignments: The specific output wells to use for each slat (if not provided, the script will automatically assign wells).
    This can be either a list of tuples (plate number, well name) or a dictionary of tuples.
    :param unique_transfer_volume_for_plates: Dictionary assigning a special transfer volume for certain plates (supersedes all other settings)
    :param output_plate_size: Either '96' or '384' for the output plate size
    :param center_only_well_pattern: Set to true to force output wells to be in the center of the plate.  This is only available for 96-well plates.
    :param generate_plate_visualization: Set to true to generate a graphic showing the positions and contents of each well in the output plates
    :param plate_viz_type: Set to 'barcode' to show a barcode of the handle types in each well,
    'pie' to show a pie chart of the handle types or 'stacked_barcode' to show a more in-detail view
    :param destination_well_max_volume: The maximum total volume that can be transferred to a well in the output plate (in uL)
    :param normalize_volumes: Set to True to normalize the volumes in each slat mixture (by adding water to the maximum volume)
    :param color_output_wells: Set to True to add a color border to each well according to the slat's layer color or unique color (if available)
    :return: Pandas dataframe corresponding to output ech handler command list
    """

    # echo command prep
    output_command_list = []
    output_well_list = []
    output_plate_num_list = []
    output_well_descriptor_dict = {}
    all_plates_needed = set()
    roundup_warning_fired = False

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
            print(Fore.BLUE + 'Too many slats for one plate, splitting into multiple plates.' + Fore.RESET)
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

        if transfer_volume_multiplier_for_slats is not None and slat_name in transfer_volume_multiplier_for_slats:
            slat_multiplier = transfer_volume_multiplier_for_slats[slat_name]
        else:
            slat_multiplier = 1

        for (handle_num, handle_data), handle_side in zip(slat_h2_data + slat_h5_data, ['h2'] * len(slat_h2_data) + ['h5'] * len(slat_h2_data)):

            if handle_data['category'] == 'SKIP': # specially marked handle that will be skipped entirely from the echo command list
                continue

            try:
                all_plates_needed.add(handle_data['plate'])
            except KeyError: #if 'plate' not in handle_data:
                if output_empty_wells:  # this is the case where a placeholder handle is used (no plate available).
                    #  If the user indicates they want to manually add in these handles,
                    #  this will output placeholders for the specific wells that need manual handling.
                    output_command_list.append([slat_name + '_%s_staple_%s' % (handle_side, handle_num),
                                                'MANUAL TRANSFER', 'MANUAL TRANSFER',
                                                output_well_list[index], reference_transfer_volume_nl*slat_multiplier,
                                                f'{destination_plate_name}_{output_plate_num_list[index]}',
                                                'MANUAL TRANSFER'])
                    continue
                else:
                    raise RuntimeError(f'The design provided has an incomplete slat: {slat_name} (slat ID {slat.ID})')

            # manages exact staple volumes here
            if unique_transfer_volume_for_plates is not None and handle_data['plate'] in unique_transfer_volume_for_plates:
                # certain plates will need different input volumes if they have different handle concentrations - users can manually specify the changes
                handle_specific_vol = unique_transfer_volume_for_plates[handle_data['plate']]*slat_multiplier
            else:
                # otherwise, extract the exact handle volumes to ensure an equal concentration w.r.t the core staples plate
                handle_specific_vol = int(reference_transfer_volume_nl * (reference_concentration_uM / handle_data['concentration']) * slat_multiplier)

            # handle volume needs to be a multiple of 25nl for echo to be able to execute...
            if handle_specific_vol % 25 != 0:
                if not roundup_warning_fired:
                    roundup_warning_fired = True
                    print(Fore.CYAN + f'WARNING: Handle volume selected for {handle_data} ({handle_specific_vol}nl) is not a multiple of 25 (Echo cannot execute volumes that are not a multiple of 25nl). The transfer volume was rounded up.')
                    print('This message will be suppressed for future occurrences.' + Fore.RESET)
                handle_specific_vol = ((handle_specific_vol // 25) + 1 ) * 25

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

        if color_output_wells:
            if slat.unique_color is not None:
                group_color = slat.unique_color
            elif slat.layer_color is not None:
                group_color = slat.layer_color
            else:
                group_color = None
        else:
            group_color = None

        output_well_descriptor_dict[(output_plate_num_list[index], output_well_list[index])] = [slat_name] + all_handle_types + [group_color] + [slat.slat_type]

    combined_df = pd.DataFrame(output_command_list, columns=['Component', 'Source Plate Name', 'Source Well',
                                                             'Destination Well', 'Transfer Volume',
                                                             'Destination Plate Name', 'Source Plate Type'])

    # Check that the total volume for all destination wells is below a maximum limit to avoid falling into source plate during transfer
    total_handle_mix_volumes_list = []
    for slat_name in slat_dict.keys():
        total_volume = sum(combined_df[combined_df["Component"].str.contains(slat_name+"_")]["Transfer Volume"])/1000
        total_handle_mix_volumes_list.append([slat_name, total_volume, total_volume <= destination_well_max_volume])

    if False in [x[2] for x in total_handle_mix_volumes_list]:
        print(Fore.RED + "WARNING: The total volume in some destination wells exceeds the specified maximum destination well volume. This could result in contamination of source wells. Consider halving your individual transfer volumes.")
        print("The offending slats are:")
        component_wells_too_high = [x for x in total_handle_mix_volumes_list if x[2] == False]
        for component_well in component_wells_too_high:
            print("Component: " + component_well[0], "Total volume: %d" % component_well[1])   
        print(Style.RESET_ALL)

    # in the case where there will be large variations between pool volumes (due to different handle concentrations), can attempt to normalize volumes to the maximum by adding additional water/buffer to wells with lower volumes.
    if normalize_volumes:
        max_volume = max([x[1] for x in total_handle_mix_volumes_list])
        total_compensation_volume_required = 0
        current_water_well = 0
        for (slat_name, total_volume, _) in total_handle_mix_volumes_list:
            if total_volume < max_volume:
                destination_well = combined_df[combined_df["Component"].str.contains(slat_name + "_")]["Destination Well"].iloc[0]
                destination_plate = combined_df[combined_df["Component"].str.contains(slat_name + "_")]["Destination Plate Name"].iloc[0]
                compensation_volume = round((max_volume - total_volume) * 1000) # a specific compensation amount is added to each individual well

                output_command_list.append([slat_name + '_volume_normalize',
                                            'WATER_PLATE', plate384[current_water_well],
                                            destination_well,
                                            compensation_volume,
                                            destination_plate,
                                            source_plate_type])
                total_compensation_volume_required += compensation_volume
                all_plates_needed.add('WATER_PLATE')

                if current_water_well == 383: # the water plate is cycled in from a round robin of wells in an attempt to prevent any of the wells from drying up during the process.
                    current_water_well = 0
                else:
                    current_water_well += 1

        combined_df = pd.DataFrame(output_command_list, columns=['Component', 'Source Plate Name', 'Source Well',
                                                                 'Destination Well', 'Transfer Volume',
                                                                 'Destination Plate Name', 'Source Plate Type'])
        if total_compensation_volume_required == 0:
            print(Fore.MAGENTA + 'No normalization required - all slats have the same total volume.' + Fore.RESET)
        else:
            # the below assumes that you are filling your water plate with 60ul of water per well, of which 20ul are usable.
            print(Fore.MAGENTA + f"Info: To normalize volumes to a total of {max_volume} μl per well, "
                                 f"a total of {total_compensation_volume_required/1000} μl of water (or 1xTEF) is required."
                                 f"  This has been split across {current_water_well} wells (fill up from well A1 to well {plate384[current_water_well-1]})." + Fore.RESET)

    combined_df.to_csv(os.path.join(output_folder, output_filename), index=False)

    if generate_plate_visualization:
        visualize_output_plates(output_well_descriptor_dict, output_plate_size, output_folder,
                                output_filename.split('.')[0],
                                slat_display_format=plate_viz_type)  # prepares a visualization of the output plates

    print(Fore.BLUE + f'Info: These are the plates you need for this echo run:{sorted(all_plates_needed)}' + Fore.RESET)

    return combined_df
