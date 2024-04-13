from crisscross.graphics.megastructures import generate_patterned_square_cco
from crisscross.core_functions.plate_handling import read_dna_plate_mapping
from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.helper_functions.standard_sequences import simpsons_anti
import os
import pandas as pd
from collections import defaultdict


if __name__ == '__main__':

    base_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/crisscross_core_plates/'

    seq_1 = simpsons_anti['Bart']
    seq_2 = simpsons_anti['Edna']
    seq_3 = simpsons_anti['Flanders']
    pattern = generate_patterned_square_cco('diagonal_octahedron_top_corner')
    pattern_biotin = generate_patterned_square_cco('biotin_patterning')

    slat_map, _, _ = generate_standard_square_slats(32)
    core_slat_plate = read_dna_plate_mapping(os.path.join(base_folder, 'sw_src002_slatcore.xlsx'))

    seq_dict = defaultdict(dict)
    for i in range(pattern.shape[0]):
        for j in range(pattern.shape[1]):  # assumes that the staples will be attached to the y-slats
            slat_pos_id = j+1
            core_name = 'slatcore-%s-h2ctrl' % slat_pos_id
            core_sequence = core_slat_plate['sequence'][core_slat_plate['name'].str.contains(core_name)].values[0]
            if pattern[i, j] == 1:
                seq_dict[slat_pos_id][1] = core_sequence + seq_1
            elif pattern[i, j] == 2:
                seq_dict[slat_pos_id][2] = core_sequence + seq_2

            if pattern_biotin[i, j] == 3:
                seq_dict[slat_pos_id][3] = core_sequence + seq_3

    pd_array = pd.DataFrame.from_dict(seq_dict, orient='index')



