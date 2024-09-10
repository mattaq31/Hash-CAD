import pandas as pd
import os
from colorama import Fore
from crisscross.helper_functions.plate_constants import plate96, plate384, plate96_center_pattern


# TODO: prepare visualization to help identify wells post generation
def convert_slats_into_echo_commands(slat_dict, destination_plate_name, output_folder, output_filename,
                                     default_transfer_volume=75, source_plate_type='384PP_AQ_BP', output_empty_wells=False,
                                     manual_plate_well_assignments=None, unique_transfer_volume_for_plates=None,
                                     output_plate_size='96', center_only_well_pattern=False):
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
    :return: Pandas dataframe corresponding to output ech handler command list
    """

    # echo command prep
    output_command_list = []
    output_well_list = []
    output_plate_num_list = []

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
        for (handle_num, handle_data), handle_side in zip(slat_h2_data + slat_h5_data, ['h2'] * len(slat_h2_data) + ['h5'] * len(slat_h2_data)):
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
            if unique_transfer_volume_for_plates is not None and handle_data['plate'] in unique_transfer_volume_for_plates:
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

    combined_df = pd.DataFrame(output_command_list, columns=['Component', 'Source Plate Name', 'Source Well',
                                                       'Destination Well', 'Transfer Volume',
                                                       'Destination Plate Name', 'Source Plate Type'])

    combined_df.to_csv(os.path.join(output_folder, output_filename), index=False)

    return combined_df
