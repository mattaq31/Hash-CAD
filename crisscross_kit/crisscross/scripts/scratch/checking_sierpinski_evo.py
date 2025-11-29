from crisscross.slat_handle_match_evolver.handle_evolution import EvolveManager
from crisscross.core_functions.megastructures import Megastructure, get_slat_key
from crisscross.helper_functions import create_dir_if_empty
import os
import glob
import re
import numpy as np
import pandas as pd
import copy

corner_file = '/Users/matt/Desktop/Sierpinski_core_with_dummy_slats.xlsx'
evo_run_folder = '/Users/matt/Desktop/Output_handles_gadgets'
output_folder = '/Users/matt/Desktop/diagnostic'
create_dir_if_empty(output_folder)
megastructure = Megastructure(import_design_file=corner_file)

excel_conditional_formatting = {'type': '3_color_scale',
                                'criteria': '<>',
                                'min_color': "#63BE7B",  # Green
                                'mid_color': "#FFEB84",  # Yellow
                                'max_color': "#F8696B",  # Red
                                'value': 0}
filenames = []
for extension in ['*.xlsx']:
    glob_path = os.path.join(evo_run_folder, extension)
    filenames.extend(glob.glob(glob_path, recursive=True))

def write_array_to_excel(writer, array, sheet_prefix):
    for layer_index in range(array.shape[-1]):
        df = pd.DataFrame(array[..., layer_index])
        sheet_name = f'{sheet_prefix}_{layer_index + 1}'
        df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
        writer.sheets[sheet_name].conditional_format(0, 0, df.shape[0], df.shape[1] - 1, excel_conditional_formatting)

# remove any duplicates
filenames = list(dict.fromkeys(filenames))
# Sort file names in Natural Order so that numbers starting with 1s don't take priority
filenames.sort(key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)])

all_arrays = []
for f_ind, file in enumerate(filenames):
    handle_array = np.zeros((megastructure.original_slat_array.shape[0], megastructure.original_slat_array.shape[1], 2))
    handle_df = pd.read_excel(file, sheet_name=None, header=None)
    for i in range(len(megastructure.layer_palette)-1):
        handle_array[..., i] = handle_df['handle_interface_%s' % (i + 1)].values
    if f_ind == 0:
        orig_array = copy.deepcopy(handle_array)
        continue
    else:
        print((orig_array-handle_array).sum())
        handle_array[(orig_array - handle_array) == 0] = 0
        all_arrays.append(handle_array)

    writer = pd.ExcelWriter(os.path.join(output_folder, 'array_%s.xlsx' % f_ind), engine='xlsxwriter')
    workbook = writer.book
    write_array_to_excel(writer, handle_array, 'handle_interface')
    writer.close()

