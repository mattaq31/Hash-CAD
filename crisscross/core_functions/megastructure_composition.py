import pandas as pd
import os
from colorama import Fore
from crisscross.helper_functions.plate_constants import plate96


def convert_slats_into_echo_commands(slat_dict, destination_plate_name, output_folder, output_filename,
                                     transfer_volume=75, source_plate_type='384PP_AQ_BP',
                                     specific_plate_wells=None, unique_transfer_volume_for_plates=None):
    """
    Converts a dictionary of slats into an echo liquid handler command list for all handles provided.
    :param slat_dict: Dictionary of slat objects
    :param destination_plate_name: The name of the design's destination output plate
    :param output_folder: The output folder to save the file to
    :param output_filename: The name of the output file
    :param transfer_volume: The transfer volume for each handle (either a single integer, or a list of integers for each individual slat)
    :param source_plate_type: The physical plate type in use
    :param specific_plate_wells: The specific output wells to use for each slat (if not provided, the script will automatically assign wells)
    :param unique_transfer_volume_for_plates: Dictionary assigning a special transfer volume for certain plates (supersedes all other settings)
    :return: Pandas dataframe corresponding to output ech handler command list
    """

    # echo command prep
    complete_list = []

    if len(slat_dict) > len(plate96):
        print(Fore.BLUE + 'Too many slats for one plate, splitting into multiple plates.')

    for index, (_, slat) in enumerate(slat_dict.items()):
        sel_plate_name = destination_plate_name
        if specific_plate_wells:  # TODO: this probably won't work if there are multiple plates
            well = specific_plate_wells[index]
        else:
            if index // len(plate96) > 0:
                sel_plate_name = destination_plate_name + '_%s' % ((index // len(plate96)) + 1)
                well = plate96[index % len(plate96)]
            else:
                well = plate96[index]

        if isinstance(transfer_volume, list):
            tv = transfer_volume[index]
        else:
            tv = transfer_volume

        for h2_num, h2 in slat.get_sorted_handles('h2'):
            if 'plate' not in h2:
                raise RuntimeError(f'The design provided has an incomplete slat: {slat.ID}')

            if unique_transfer_volume_for_plates is not None and h2['plate'] in unique_transfer_volume_for_plates:
                handle_specific_vol = unique_transfer_volume_for_plates[h2['plate']]
            else:
                handle_specific_vol = tv
            complete_list.append([slat.ID + '_h2_staple_%s' % h2_num, h2['plate'], h2['well'],
                                  well, handle_specific_vol, sel_plate_name, source_plate_type])

        for h5_num, h5 in slat.get_sorted_handles('h5'):
            if 'plate' not in h5:
                raise RuntimeError(f'The design provided has an incomplete slat: {slat.ID}')

            if unique_transfer_volume_for_plates is not None and h5['plate'] in unique_transfer_volume_for_plates:
                handle_specific_vol = unique_transfer_volume_for_plates[h5['plate']]
            else:
                handle_specific_vol = tv
            complete_list.append([slat.ID + '_h5_staple_%s' % h5_num, h5['plate'], h5['well'],
                                  well, handle_specific_vol, sel_plate_name, source_plate_type])

    combined_df = pd.DataFrame(complete_list, columns=['Component', 'Source Plate Name', 'Source Well',
                                                       'Destination Well', 'Transfer Volume',
                                                       'Destination Plate Name', 'Source Plate Type'])

    combined_df.to_csv(os.path.join(output_folder, output_filename), index=False)

    return combined_df
