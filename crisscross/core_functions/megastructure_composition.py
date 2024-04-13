import pandas as pd
import os
from crisscross.helper_functions.plate_constants import plate96


def convert_slats_into_echo_commands(slat_dict, destination_plate_name, output_folder, output_filename,
                                     transfer_volume=75, source_plate_type='384PP_AQ_BP'):

    # echo command prep
    complete_list = []
    total_wells = 0
    for _, slat in slat_dict.items():
        for h2_num, h2 in slat.get_sorted_handles('h2'):
            complete_list.append([slat.ID + '_h2_staple_%s' % h2_num, h2['plate'], h2['well'],
                                  plate96[total_wells], transfer_volume, destination_plate_name, source_plate_type])

        for h5_num, h5 in slat.get_sorted_handles('h5'):
            complete_list.append([slat.ID + '_h5_staple_%s' % h5_num, h5['plate'], h5['well'],
                                  plate96[total_wells], transfer_volume, destination_plate_name, source_plate_type])
        total_wells += 1

    combined_df = pd.DataFrame(complete_list, columns=['Component', 'Source Plate Name', 'Source Well',
                                                       'Destination Well', 'Transfer Volume',
                                                       'Destination Plate Name', 'Source Plate Type'])
    combined_df.to_csv(os.path.join(output_folder, output_filename), index=False)

    return combined_df
