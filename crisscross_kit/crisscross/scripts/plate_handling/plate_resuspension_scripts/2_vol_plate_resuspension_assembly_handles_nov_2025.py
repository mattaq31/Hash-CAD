from crisscross.helper_functions.simple_plate_visuals import visualize_plate_with_color_labels
from crisscross.helper_functions import create_dir_if_empty
from crisscross.plate_mapping import get_cutting_edge_plates, sanitize_plate_map

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


main_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Shared Experiment Files/Plate Specs and Resuspension Maps/assembly handle refill Nov 2025'
resuspension_output_folder = os.path.join(main_folder, 'manual_resuspension_maps')
master_transfer_output_folder = os.path.join(main_folder, 'refill_master_transfer_maps')
echo_working_stock_output_folder = os.path.join(main_folder, 'echo_working_stock_commands')

create_dir_if_empty(resuspension_output_folder, master_transfer_output_folder, echo_working_stock_output_folder)

target_files = [os.path.join(main_folder, 'more_assembly_handles.xlsx'), os.path.join(main_folder, 'nanocube_and_assembly_handles.xlsx')]

target_concentration = 1000
cutoff_nmole_value = 90 # anything less than this value will be resuspended to the minimum nmole value

conduct_step_1 = False
conduct_step_2 = False
conduct_step_3 = True

if conduct_step_1:
    # STEP 1: RESUSPENDING DRY PLATES
    master_concentration_record = []
    for target_file in target_files:

        # reads in raw data
        spec_df = pd.read_excel(target_file, sheet_name=None)['Plate Specs']
        plate_names = spec_df['Plate Name'].unique()

        for plate_name in plate_names:
            if 'MAD' in plate_name: # already came resuspended
                continue
            selected_plate_df = spec_df[spec_df['Plate Name'] == plate_name]
            nmole_values = selected_plate_df['nmoles'].values
            plate_wells = selected_plate_df['Well Position'].values

            # outlier analysis
            median = np.median(nmole_values)
            mad = np.median(np.abs(nmole_values - median))
            modified_z_score = 0.6745 * (nmole_values - median) / mad
            outliers = nmole_values[np.abs(modified_z_score) > 3.5]
            min_nmole = np.min(nmole_values) # not taking into account outliers
            min_nmole_no_outliers = np.min(nmole_values[np.abs(modified_z_score) <= 3.5])

            # true volume required if the whole plate was being resuspended accurately
            true_volume_required = (nmole_values / target_concentration) * 1000

            # two volume values selected for easier pipetting
            min_volume_required = (min_nmole_no_outliers / target_concentration) * 1000
            norm_volume_required = (cutoff_nmole_value / target_concentration) * 1000

            low_volume_dict = {}
            special_well_volume_dict = {}
            low_volume_count = 0
            outlier_volume_count = 0
            for well_index, nmole in enumerate(nmole_values):
                well_name = plate_wells[well_index]

                if well_name[1] == '0': # formatting fix
                    well_name = well_name[0] + well_name[2]

                if nmole in outliers: # if outlier, resuspend accurately
                    low_volume_dict[well_name] = 'red'
                    special_well_volume_dict[well_name] = round((nmole / target_concentration) * 1000, 1)
                    outlier_volume_count += 1
                    master_concentration_record.append(target_concentration)

                elif nmole < cutoff_nmole_value: # if low nmole, resuspend to min nmole
                    low_volume_dict[well_name] = 'blue'
                    low_volume_count += 1
                    master_concentration_record.append((nmole/min_volume_required) * 1000)
                else: # otherwise, resuspend to selected threshold
                    actual_concentration = (nmole/norm_volume_required) * 1000

                    if actual_concentration > target_concentration * 1.4: # should also consider really high nmoles as outliers
                        low_volume_dict[well_name] = 'red'
                        special_well_volume_dict[well_name] =  round((nmole / target_concentration) * 1000, 1)
                        outlier_volume_count += 1
                        master_concentration_record.append(target_concentration)
                    else:
                        low_volume_dict[well_name] = 'green'
                        master_concentration_record.append(actual_concentration)

            visualize_plate_with_color_labels('384' if 'P3653_MA' in plate_name else '96', low_volume_dict,
                                              direct_show=False,
                                              well_label_dict = special_well_volume_dict,
                                              plate_title = f'{plate_name} (low nmole cutoff = {cutoff_nmole_value},'
                                                            f' low nmole count = {low_volume_count}, '
                                                            f'outlier count = {outlier_volume_count}, '
                                                            f'Standard nmole count = {len(nmole_values) - low_volume_count - outlier_volume_count},'
                                                            f' target conc. = {target_concentration}μM)',
                                              color_label_dict={'blue': f'Low nmole wells ({min_volume_required:.2f}μl)',
                                                                'red': f'Outlier wells',
                                                                'green': f'Standard nmole wells ({norm_volume_required:.2f}μl)'},
                                              save_file=f'{plate_name}_resuspension_map', save_folder=resuspension_output_folder)

    print('Minimum concentration in uM after resuspension:', np.min(master_concentration_record))
    fig, ax = plt.subplots(figsize=(12, 8))
    # Overlay bar plot (make sure alpha is higher than KDE plot)
    sns.histplot(master_concentration_record, ax=ax, bins=40, kde=True, line_kws={'linewidth': 6})
    plt.xlabel('Concentration/uM')
    plt.savefig(os.path.join(resuspension_output_folder, f'full_resuspension_concentration_distribution.png'), bbox_inches='tight', dpi=300)
    plt.show()

# STEP 2: REFILLING MASTER PLATES
if conduct_step_2:
    for target_file in target_files:
        # reads in raw data
        spec_df = pd.read_excel(target_file, sheet_name=None)['Plate Specs']
        plate_names = spec_df['Plate Name'].unique()
        for plate_name in plate_names:
            if 'MAD' in plate_name or 'P3653' in plate_name:  # already came resuspended, or already in 384-well format
                continue
            selected_plate_df = spec_df[spec_df['Plate Name'] == plate_name]
            sequence_names = selected_plate_df['Sequence Name'].values
            plate_wells = selected_plate_df['Well Position'].values

            well_dict = {}
            colour_dict = {}

            well_dict_96 = {}
            colour_dict_96 = {}

            for well_index, seq_name in enumerate(sequence_names):
                well_name = plate_wells[well_index]
                if well_name[1] == '0': # formatting fix
                    well_name = well_name[0] + well_name[2]

                colour_dict[seq_name.split('Refill ')[-1]] = '#ADD8E6'
                well_dict[seq_name.split('Refill ')[-1]] = well_name

                well_dict_96[well_name] = seq_name.split('Refill ')[-1]
                colour_dict_96[well_name] = '#ADD8E6'

            visualize_plate_with_color_labels('384', colour_dict,
                                              direct_show=False,
                                              well_label_dict = well_dict,
                                              plate_title = f'{plate_name} transfer map from 96-well refill to 384-well master plate',
                                              color_label_dict={'#ADD8E6': f'Transfer from the indicated 96-well ID to this slot'},
                                              save_file=f'{plate_name}_master_stock_restock_map', save_folder=master_transfer_output_folder)

            visualize_plate_with_color_labels('96', colour_dict_96,
                                              direct_show=False,
                                              well_label_dict = well_dict_96,
                                              plate_title = f'{plate_name} transfer map from 96-well refill to 384-well master plate',
                                              color_label_dict={'#ADD8E6': f'Transfer from the coloured well to the 384-well ID indicated'},
                                              save_file=f'{plate_name}_master_stock_restock_map_96well', save_folder=master_transfer_output_folder)

if conduct_step_3: # this prepares the echo commands to transfers the masters to working stocks for dilution to 200uM
    _, antihandle_plates, handle_plates, _ = get_cutting_edge_plates()

    transfer_volume = 8000  # 8ul
    master_command_list_A = []
    master_command_list_B = []

    for group in [handle_plates, antihandle_plates]:
        for plate, plate_name in zip(group.plates, group.plate_names):
            source_plate = sanitize_plate_map(plate_name)
            dest_plates = [sanitize_plate_map(plate_name) + '_working_stock_%s' % pos for pos in ['A', 'B']]
            for ind, dest_plate in enumerate(dest_plates):
                output_command_list = []
                for row in plate.iterrows():
                    if isinstance(row[1]['name'], str):
                        source_well = row[1]['well']
                        dest_well = row[1]['well']
                        name = row[1]['name'] +  f'_%s'  % ['A', 'B'][ind]
                        output_command_list.append([name, source_plate, source_well, dest_well, transfer_volume, dest_plate, '384PP_AQ_BP'])
                        if ind == 0:
                            master_command_list_A.append([name, source_plate, source_well, dest_well, transfer_volume, dest_plate, '384PP_AQ_BP'])
                        else:
                            master_command_list_B.append([name, source_plate, source_well, dest_well, transfer_volume, dest_plate, '384PP_AQ_BP'])

                combined_df = pd.DataFrame(output_command_list, columns=['Component', 'Source Plate Name', 'Source Well',
                                                                         'Destination Well', 'Transfer Volume',
                                                                         'Destination Plate Name', 'Source Plate Type'])
                combined_df.to_csv(os.path.join(echo_working_stock_output_folder, f'{dest_plate}_echo_commands.csv'), index=False)

    master_df_A = pd.DataFrame(master_command_list_A, columns=['Component', 'Source Plate Name', 'Source Well',
                                                               'Destination Well', 'Transfer Volume',
                                                               'Destination Plate Name', 'Source Plate Type'])

    master_df_A.to_csv(os.path.join(echo_working_stock_output_folder, f'all_echo_commands_first_working_stocks.csv'), index=False)

    master_df_B = pd.DataFrame(master_command_list_B, columns=['Component', 'Source Plate Name', 'Source Well',
                                                               'Destination Well', 'Transfer Volume',
                                                               'Destination Plate Name', 'Source Plate Type'])

    master_df_B.to_csv(os.path.join(echo_working_stock_output_folder, f'all_echo_commands_second_working_stocks.csv'), index=False)
