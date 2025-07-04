import os
from crisscross.helper_functions import base_directory
import pandas as pd
from crisscross.helper_functions.simple_plate_visuals import visualize_plate_with_color_labels

t1 = os.path.join(base_directory, 'core_plates', 'spec_sheets', 'P3643_specs.xlsx')
t2 = os.path.join(base_directory, 'cargo_plates', 'spec_sheets', 'P3628_specs.xlsx')

target_files = [t1, t2]
target_concentrations = [1000, 200]

for target_file, target_concentration in zip(target_files, target_concentrations):
    spec_df = pd.read_excel(target_file, sheet_name=None)['Plate Specs']
    nmole_values = spec_df['nmoles'].values
    plate_wells = spec_df['Well Position'].values
    volume_required = (nmole_values / target_concentration) * 1000

    visual_dict = {}
    numeric_dict = {}
    for well_index, vol in enumerate(volume_required):
        well_name = plate_wells[well_index]
        if well_name[1] == '0':
            well_name = well_name[0] + well_name[2]
        visual_dict[well_name] = '#40E0D0'
        numeric_dict[well_name] = round(vol, 2)

    visualize_plate_with_color_labels('384', visual_dict,
                                      direct_show=False,
                                      well_label_dict=numeric_dict,
                                      plate_title = f'{spec_df["Plate Name"][0]} (numbers = μl of UPW to add to achieve a target concentration of {target_concentration}μM)',
                                      save_file=f'{spec_df["Plate Name"][0]}_resuspension_map', save_folder='/Users/matt/Desktop')

    # convert the well position and volumes to a pandas df and save to csv file
    df = pd.DataFrame.from_dict(numeric_dict, orient='index', columns=['Volume (μl)'])
    df.index.name = 'Well Position'
    df.to_csv(f'/Users/matt/Desktop/{spec_df["Plate Name"][0]}_resuspension_volumes.csv')


