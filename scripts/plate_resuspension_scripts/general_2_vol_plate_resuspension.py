import os
from crisscross.helper_functions import base_directory
import pandas as pd
from crisscross.helper_functions.simple_plate_visuals import visualize_plate_with_color_labels
import numpy as np

t1 = os.path.join(base_directory, 'core_plates', 'spec_sheets', 'P3643_specs.xlsx')
target_files = [t1]
target_concentrations = [1000]
cutoff_nmole_value = 90 # anything less than this value will be resuspended to the minimum nmole value
norm_nmole = 100 # this particular plate was ordered at 100nmol scale

for target_file, target_concentration in zip(target_files, target_concentrations):
    spec_df = pd.read_excel(target_file, sheet_name=None)['Plate Specs']
    nmole_values = spec_df['nmoles'].values
    plate_wells = spec_df['Well Position'].values

    volume_required = (nmole_values / target_concentration) * 1000
    min_nmole = np.min(nmole_values)
    min_volume_required = (min_nmole / target_concentration) * 1000
    norm_volume_required = (norm_nmole / target_concentration) * 1000

    low_volume_dict = {}
    low_volume_count = 0
    for well_index, nmole in enumerate(nmole_values):
        well_name = plate_wells[well_index]
        if well_name[1] == '0':
            well_name = well_name[0] + well_name[2]

        if nmole < cutoff_nmole_value:
            low_volume_dict[well_name] = 'red'
            low_volume_count += 1
        else:
            low_volume_dict[well_name] = '#D3D3D3'


    visualize_plate_with_color_labels('384', low_volume_dict,
                                      direct_show=False,
                                      plate_title = f'{spec_df["Plate Name"][0]} (low nmole cutoff = {cutoff_nmole_value}, low nmole count = {low_volume_count}, target conc. = {target_concentration}μM)',
                                      color_label_dict={'red': f'Low nmole wells ({min_volume_required:.2f}μl)',
                                                        '#D3D3D3': f'Standard nmole wells ({norm_volume_required:.2f}μl)'},
                                      save_file=f'{spec_df["Plate Name"][0]}_resuspension_map', save_folder='/Users/matt/Desktop')

