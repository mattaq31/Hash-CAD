import pandas as pd
import numpy as np
from crisscross.helper_functions.simple_plate_visuals import visualize_plate_with_color_labels

files = ['/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/crisscross_code/assembly_handle_plates/new_assembly_handle_library_dec_2024/IDT_plate_specs/3601-3603.xlsx',
         '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/crisscross_code/assembly_handle_plates/new_assembly_handle_library_dec_2024/IDT_plate_specs/3604-3606.xlsx']

plate_targets = ['P3601_MA', 'P3602_MA', 'P3603_MA', 'P3604_MA']  # problem plates
target_concentration = 100 # uM

for index, f in enumerate(files):
    if index == 0:
        spec_df = pd.read_excel(f, sheet_name=None)['Plate Specs']
    else:
        spec_df = pd.concat([spec_df, pd.read_excel(f, sheet_name=None)['Plate Specs']])

# Special treatment FOR P3605/6 since they have very similar nmole values for some reason
nmole_values = spec_df['nmoles'].values
unique_values_at_start = np.unique(nmole_values)
consistent_nmole_values = spec_df[(spec_df['Plate Name'] == 'P3605_MA') | (spec_df['Plate Name'] == 'P3606_MA')]['nmoles'].values
percentage_errors = (np.abs(4 - consistent_nmole_values)/4) * 100
max_nmole_error = np.abs(4 - consistent_nmole_values).max()
vol_required = (4/target_concentration)*1000
error_concentration = (max_nmole_error/vol_required)*1000

print(f'For plates P3605_MA and P3606_MA, can resuspend all wells with a volume of '
      f'{vol_required} ul to achieve a concentration of 100uM.  '
      f'The maximum concentration error will be +-{error_concentration:.2f}uM '
      f'i.e. {(error_concentration/target_concentration)*100:.2f}%')

# for other plates, we're gonna be resuspending using a 12-well multichannel pipette.
# Ideally, we'd want to use the same volume for each well, but the values are too different to ignore

# initially I thought we could average the value of groups of 12, but the wells vary too much for this to be viable
row_periodicity = 24
style_labels = ['Integra Method, Row wells 1-12', 'Integra Method, Row wells 13-24', 'Multichannel Method, Odd wells', 'Multichannel Method, Even wells']
averaging_method = False
if averaging_method:
    for plate in plate_targets:
        nmole_values = spec_df[spec_df['Plate Name'] == plate]['nmoles'].values
        start_point = 0
        for end_point in range(row_periodicity, len(nmole_values), row_periodicity):
            selected_values = nmole_values[start_point:end_point]

            # there are two pipetting styles:
            # style 1: resuspend 12 wells next to each other using the integra pipette
            style_1_g1 = selected_values[:12]
            style_1_g2 = selected_values[12:]

            # style 2: resuspend alternating wells using a standard multichannel pipette
            style_2_g1 = selected_values[::2]
            style_2_g2 = selected_values[1::2]

            for index, combined_group in enumerate([style_1_g1, style_1_g2, style_2_g1, style_2_g2]):

                average_nmole = np.average(combined_group)
                vol_suggested = (average_nmole / target_concentration) * 1000
                all_concentration_errors = ((average_nmole - combined_group) / vol_suggested) * 1000
                all_concentration_percentage_errors = (all_concentration_errors / target_concentration) * 100
                formatted_errors = ', '.join([f'{error:.2f}' for error in all_concentration_percentage_errors])
                print(style_labels[index])
                print(f'Average nmole quantity: {average_nmole:.2f}, '
                      f'Suggested volume: {vol_suggested:.2f}ul,'
                      f'\nerror % for each well: {formatted_errors},\n'
                      f'Max error: {all_concentration_errors.max():.2f}uM/{all_concentration_percentage_errors.max():.2f}%,')
                print('---')
                if index == 1:
                    print('%%%%')

            start_point = end_point


# instead, our new approach is to split wells into two: those that are close to or higher than 10nmol (target)
# and those that are much lower (depending on the minimum)
# we will resuspend the higher ones as if they all had 10 nmol and the lower ones as if they had the minimum value
# this way, we will never have low-concentration wells but we will have several wells with a higher concentration
# we are fine with the higher concentration since all staples are added in excess.

cutoff_nmole_value = 9.5 # anything less than this value will be resuspended to the minimum nmole value

for plate in plate_targets:
    nmole_values = spec_df[spec_df['Plate Name'] == plate]['nmoles'].values
    plate_wells = spec_df[spec_df['Plate Name'] == plate]['Well Position'].values
    min_nmole = np.min(nmole_values)
    min_volume_required = (min_nmole / target_concentration) * 1000
    norm_volume_required = (10 / target_concentration) * 1000

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
                                      plate_title = f'{plate} (low nmole cutoff = {cutoff_nmole_value}, low nmole count = {low_volume_count}, target conc. = {target_concentration}μM)',
                                      color_label_dict={'red': f'Low nmole wells ({min_volume_required:.2f}μl)',
                                                        '#D3D3D3': f'Standard nmole wells ({norm_volume_required:.2f}μl)'},
                                      save_file=f'{plate}_volume_resuspension', save_folder='/Users/matt/Desktop')


