# NOW SUPERSEDED BY CLI FUNCTION (plate_resuspension.py)

import os
from crisscross.helper_functions import base_directory, create_dir_if_empty
import pandas as pd
from crisscross.helper_functions.simple_plate_visuals import visualize_plate_with_color_labels
from tqdm import tqdm
from math import floor
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import platform


# consistent figure formatting between mac, windows and linux
if platform.system() == 'Darwin':
    plt.rcParams.update({'font.sans-serif': 'Helvetica'})
elif platform.system() == 'Windows':
    plt.rcParams.update({'font.sans-serif': 'Arial'})
else:
    plt.rcParams.update({'font.sans-serif': 'DejaVu Sans'}) # should work with linux


input_dir = os.path.join(base_directory, 'assembly_handle_plates/new_assembly_handle_library_orders/maximal_order/IDT_spec_sheets')
input_dir = '/Users/matt/Desktop/input_sheets'

# get all excel files in the above directory
input_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith('.xlsx')]
target_concentrations = [1000] * len(input_files)
output_directory = '/Users/matt/Desktop/Eppendorf_resuspension_maps'
map_directory = os.path.join(output_directory, 'maps')
script_directory = os.path.join(output_directory, 'scripts')

create_dir_if_empty(output_directory, map_directory, script_directory)

min_volume = np.inf
max_volume = 0

volume_dist = []

for target_file, target_concentration in tqdm(zip(input_files, target_concentrations), total=len(input_files), desc='Processing files...'):
    spec_df = pd.read_excel(target_file, sheet_name=None)['Plate Specs']
    # get all unique names in the 'Plate Name' column
    plate_names = spec_df['Plate Name'].unique()
    for plate_name in plate_names:
        selected_plate_df = spec_df[spec_df['Plate Name'] == plate_name]
        nmole_values = selected_plate_df['nmoles'].values
        plate_wells = selected_plate_df['Well Position'].values
        volume_required = (nmole_values / target_concentration) * 1000

        # cap all volumes to 120
        volume_required[volume_required > 120] = 120

        visual_dict = {}
        numeric_dict = {}

        max_volume = max(max_volume, np.max(volume_required))
        min_volume = min(min_volume, np.min(volume_required))
        volume_dist.extend(volume_required.tolist())
        for well_index, vol in enumerate(volume_required):
            well_name = plate_wells[well_index]
            if well_name[1] == '0':
                well_name = well_name[0] + well_name[2]
            visual_dict[well_name] = '#40E0D0'

            # how to use the floor function in python
            numeric_dict[well_name] = floor(vol * 10)/10

        visualize_plate_with_color_labels('384', visual_dict,
                                          direct_show=False,
                                          well_label_dict=numeric_dict,
                                          plate_title = f'{plate_name} (numbers = μl of UPW to add to achieve a target concentration of {target_concentration}μM)',
                                          save_file=f'{plate_name}_resuspension_map', save_folder=map_directory)

        # convert the well position and volumes to a pandas df and save to csv file
        output_volume_df = pd.DataFrame.from_dict(numeric_dict, orient='index', columns=['Volume'])
        output_volume_df = output_volume_df.reset_index()
        output_volume_df.columns = ['Destination', 'Volume']
        output_volume_df['Rack'] = 1
        output_volume_df['Source'] = 1
        output_volume_df['Rack 2'] = 1
        output_volume_df['Tool'] = 2
        output_volume_df = output_volume_df[['Rack', 'Source', 'Rack 2', 'Destination', 'Volume', 'Tool']]

        if len(output_volume_df) > 96:
            # export in groups of 96
            for index, i in enumerate(range(0, len(output_volume_df), 96)):
                output_volume_df.iloc[i:i + 96].to_csv(os.path.join(script_directory, f'{plate_name}_resuspension_volumes_{index+1}.csv'), header=['Rack', 'Source', 'Rack', 'Destination', 'Volume', 'Tool'], index=False)
        else:
            output_volume_df.to_csv(os.path.join(script_directory, f'{plate_name}_resuspension_volumes.csv'), header=['Rack', 'Source', 'Rack', 'Destination', 'Volume', 'Tool'], index=False)

fig, ax = plt.subplots(figsize=(12, 8))

# Overlay bar plot (make sure alpha is higher than KDE plot)
sns.histplot(volume_dist, ax=ax, bins=40, kde=True, line_kws={'linewidth': 6})

plt.xlabel('Volume (μl)', fontsize=20)
plt.ylabel('Frequency', fontsize=20)
plt.title(f'Distribution of resuspension volumes (target concentration 1000 μM)', fontsize=30)
plt.xticks(fontsize=18)
plt.yticks(fontsize=18)
plt.tight_layout()
plt.savefig(os.path.join(output_directory, 'resuspension_volume_distribution.png'), dpi=300)
plt.show()
print('Min resuspension volume (ul):', min_volume)
print('Max resuspension volume (ul):', max_volume)
