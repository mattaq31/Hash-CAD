import os
import pandas as pd
from crisscross.helper_functions.simple_plate_visuals import visualize_plate_with_color_labels
from crisscross.helper_functions import create_dir_if_empty
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


main_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Shared Experiment Files/Plate Specs and Resuspension Maps/assembly handle refill Nov 2025'
output_folder = os.path.join(main_folder, 'manual_resuspension_maps')
create_dir_if_empty(output_folder)

target_files = [os.path.join(main_folder, 'more_assembly_handles.xlsx'), os.path.join(main_folder, 'nanocube_and_assembly_handles.xlsx')]

target_concentration = 1000
cutoff_nmole_value = 80 # anything less than this value will be resuspended to the minimum nmole value

master_concentration_record = []
for target_file in target_files:

    # reads in raw data
    spec_df = pd.read_excel(target_file, sheet_name=None)['Plate Specs']
    plate_names = spec_df['Plate Name'].unique()

    for plate_name in plate_names:
        if 'MAD' in plate_name:
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
        volume_required = (nmole_values / target_concentration) * 1000


        # two volume values selected for easier pipetting
        min_volume_required = (min_nmole_no_outliers / target_concentration) * 1000
        norm_volume_required = (cutoff_nmole_value / target_concentration) * 1000

        low_volume_dict = {}
        special_well_volume_dict = {}
        low_volume_count = 0
        outlier_volume_count = 0
        for well_index, nmole in enumerate(nmole_values):
            well_name = plate_wells[well_index]
            if well_name[1] == '0':
                well_name = well_name[0] + well_name[2]

            if nmole in outliers:
                low_volume_dict[well_name] = 'red'
                special_well_volume_dict[well_name] = (nmole / target_concentration) * 1000
                outlier_volume_count += 1
                master_concentration_record.append(target_concentration)

            elif nmole < cutoff_nmole_value:
                low_volume_dict[well_name] = 'blue'
                low_volume_count += 1
                master_concentration_record.append((nmole/min_volume_required) * 1000)
            else:
                actual_concentration = (nmole/norm_volume_required) * 1000
                if actual_concentration > target_concentration * 1.4:
                    low_volume_dict[well_name] = 'red'
                    special_well_volume_dict[well_name] =  (nmole / target_concentration) * 1000
                    outlier_volume_count += 1
                    master_concentration_record.append(target_concentration)
                else:
                    low_volume_dict[well_name] = 'green'
                    master_concentration_record.append(actual_concentration)

        # visualize_plate_with_color_labels('384' if 'P3653_MA' in plate_name else '96', low_volume_dict,
        #                                   direct_show=False,
        #                                   well_label_dict = special_well_volume_dict,
        #                                   plate_title = f'{plate_name} (low nmole cutoff = {cutoff_nmole_value},'
        #                                                 f' low nmole count = {low_volume_count}, '
        #                                                 f'outlier count = {outlier_volume_count}, '
        #                                                 f'Standard nmole count = {len(nmole_values) - low_volume_count - outlier_volume_count},'
        #                                                 f' target conc. = {target_concentration}μM)',
        #                                   color_label_dict={'blue': f'Low nmole wells ({min_volume_required:.2f}μl)',
        #                                                     'red': f'Outlier wells',
        #                                                     'green': f'Standard nmole wells ({norm_volume_required:.2f}μl)'},
        #                                   save_file=f'{plate_name}_resuspension_map', save_folder=output_folder)

print('Minimum concentration in uM after resuspension:', np.min(master_concentration_record))
fig, ax = plt.subplots(figsize=(12, 8))
# Overlay bar plot (make sure alpha is higher than KDE plot)
sns.histplot(master_concentration_record, ax=ax, bins=40, kde=True, line_kws={'linewidth': 6})
plt.xlabel('Concentration/uM')
plt.savefig(os.path.join(output_folder, f'full_resuspension_concentration_distribution.png'), bbox_inches='tight', dpi=300)
plt.show()
