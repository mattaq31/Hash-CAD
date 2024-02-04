import pandas as pd
from crisscross.helper_functions import plate_maps


def read_dna_plate_mapping(filename, data_type='2d_excel', plate_size=384):

    if plate_size == 96:
        plate = plate_maps.plate96
    else:
        plate = plate_maps.plate384

    # all staples for the standard slat, including control h2/h5 sequences
    if data_type == '2d_excel':
        all_data = pd.ExcelFile(filename)
        names = all_data.parse("Names", index_col=0)
        sequences = all_data.parse("Sequences", index_col=0)
        descriptions = all_data.parse("Descriptions", index_col=0)
        combined_dict = {}
        for entry in plate:
            n, s, d = names[entry[1:]][entry[0]], sequences[entry[1:]][entry[0]], descriptions[entry[1:]][entry[0]]
            valid_vals = [pd.isna(n), pd.isna(s), pd.isna(d)]
            if sum(valid_vals) == 3:
                continue
            elif sum(valid_vals) > 0:
                raise RuntimeError('The sequence file provided has an inconsistency in entry %s' % entry)
            combined_dict[entry] = {'well': entry,
                                    'name': n,
                                    'sequence': s,
                                    'description': d}

        return pd.DataFrame.from_dict(combined_dict, orient='index')
    else:
        raise ValueError('Invalid data type for plate input')


# just for testing
if __name__ == '__main__':
    core_slat_plate = read_dna_plate_mapping('/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/crisscross_core_plates/sw_src002_slatcore.xlsx')
    core_seed_plate = read_dna_plate_mapping('/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/crisscross_core_plates/sw_src001_seedcore.xlsx')
