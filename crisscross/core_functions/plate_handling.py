import math
import os
from collections import defaultdict
from string import ascii_uppercase
import pandas as pd

from crisscross.helper_functions import plate_maps


def add_data_to_plate_df(letters, column_total, data_dict):
    """
    Creates an empty plate (i.e. with rows/columns premade) and inserts provided data  dict.
    :param letters: Letters to use for rows.
    :param column_total: Total amount of columns (numbers)
    :param data_dict: Nested dictionary containing data to input into plate
    (keys are letters, values are dictionaries with numbers as keys)
    :return: Updated plate
    """
    plate_df = pd.DataFrame(index=letters, columns=[str(i) for i in range(1, column_total + 1)])

    if len(data_dict) == 0:
        return plate_df
    else:
        plate_df.update(pd.DataFrame.from_dict(data_dict, orient='index'))
        return plate_df


def read_dna_plate_mapping(filename, data_type='2d_excel', plate_size=384):
    """
    Reads a DNA plate mapping file and returns a dataframe with the data.
    :param filename: Filename to read (full path)
    :param data_type: Type of data - currently only supports 2d_excel and IDT_order
    :param plate_size: Either 96 or 384-well plate sizes
    :return: Dataframe containing all data
    """
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
    elif data_type == 'IDT_order':
        all_data = pd.read_excel(filename)
        all_data.columns = ['well', 'name', 'sequence', 'description']
        return all_data
    else:
        raise ValueError('Invalid data type for plate input')


def generate_new_plate_from_slat_handle_df(sequence_df, folder, filename, names_df=None, notes_df=None,
                                           data_type='2d_excel', plate_size=384):
    # TODO: this definitely could be done more elegantly - revise when new functionality needs to be added
    # TODO: make it easy to also convert IDT-format tables to 2D tables too
    """
    Generates a new plate from a dataframe containing sequences, names and notes, then saves it to file.
    :param sequence_df: Main sequence data to export.
    Columns should contain different sequence categories and rows should be indexed properly.
    :param folder: Output folder.
    :param filename: Output filename.
    :param names_df: Any names to apply to each sequence (optional).
    :param notes_df: Any notes to link with each sequence (optional).
    :param data_type: Either 2d_excel (2d output array) or IDT_order (for IDT order form).
    :param plate_size: 96 or 384
    :return: N/A
    """
    if plate_size == 96:
        plate = plate_maps.plate96
        max_row = 12
        letters = [a for a in ascii_uppercase[:8]]
    else:
        plate = plate_maps.plate384
        max_row = 24
        letters = [a for a in ascii_uppercase[:16]]

    # all staples for the standard slat, including control h2/h5 sequences
    if data_type == '2d_excel':

        name_dict = defaultdict(dict)
        seq_dict = defaultdict(dict)
        desc_dict = defaultdict(dict)
        row_num = 0
        for col in sequence_df.columns:
            # num_seqs = sequence_df[col].count()
            sequence_tracker = 0
            for i in sequence_df[col].index:
                seq = sequence_df[col][i]
                if isinstance(seq, float) and math.isnan(seq):
                    continue
                letter_id, num_id = plate[row_num * max_row + sequence_tracker][0], plate[row_num * max_row + sequence_tracker][1:]

                seq_dict[letter_id][num_id] = seq
                if names_df is not None:
                    name_dict[letter_id][num_id] = names_df[col][i]
                if notes_df is not None:
                    desc_dict[letter_id][num_id] = notes_df[col][i]
                sequence_tracker += 1
            row_num += sequence_tracker // max_row + 1

        seq_dict = add_data_to_plate_df(letters, max_row, seq_dict)
        name_dict = add_data_to_plate_df(letters, max_row, name_dict)
        desc_dict = add_data_to_plate_df(letters, max_row, desc_dict)

        with pd.ExcelWriter(os.path.join(folder, filename)) as writer:
            seq_dict.to_excel(writer, sheet_name='Sequences', index_label=filename.split('.')[0])
            name_dict.to_excel(writer, sheet_name='Names', index_label=filename.split('.')[0])
            desc_dict.to_excel(writer, sheet_name='Descriptions', index_label=filename.split('.')[0])

    elif data_type == 'IDT_order':
        output_dict = defaultdict(list)
        position = 0
        for col in sequence_df.columns:
            for col_index in sequence_df[col].index:
                if isinstance(sequence_df[col][col_index], float) and math.isnan(sequence_df[col][col_index]):
                    continue
                output_dict['WellPosition'].append(plate[position])
                output_dict['Name'].append(names_df[col][col_index] if names_df is not None else 'seq_%s' % position)
                output_dict['Sequence'].append(sequence_df[col][col_index])
                output_dict['Notes'].append(notes_df[col][col_index] if notes_df is not None else None)
                position += 1
        output_df = pd.DataFrame.from_dict(output_dict, orient='columns')
        with pd.ExcelWriter(os.path.join(folder, filename)) as writer:
            output_df.to_excel(writer, sheet_name='IDT Order', index=False)
    else:
        raise ValueError('Invalid data type for plate input')


# TODO: need to figure out mapping of each specific slatcore/seed plate to see how to combine things together...
# just for testing
if __name__ == '__main__':
    seed_plate_corner = read_dna_plate_mapping('/Users/matt/Desktop/Book2.xlsx', data_type='IDT_order')

    plate = plate_maps.plate384
    max_row = 24
    letters = [a for a in ascii_uppercase[:16]]

    name_dict = defaultdict(dict)
    seq_dict = defaultdict(dict)
    desc_dict = defaultdict(dict)
    row_num = 0
    for index, row in seed_plate_corner.iterrows():
        letter_id = row['well'][0]
        num_id = row['well'][1:]
        seq_dict[letter_id][num_id] = row['sequence']
        name_dict[letter_id][num_id] = row['name']
        desc_dict[letter_id][num_id] = row['description']

    seq_dict = add_data_to_plate_df(letters, max_row, seq_dict)
    name_dict = add_data_to_plate_df(letters, max_row, name_dict)
    desc_dict = add_data_to_plate_df(letters, max_row, desc_dict)

    with pd.ExcelWriter('/Users/matt/Desktop/P2854_CW_seed_plug_center.xlsx') as writer:
        seq_dict.to_excel(writer, sheet_name='Sequences', index_label='P3339_JL')
        name_dict.to_excel(writer, sheet_name='Names', index_label='P3339_JL')
        desc_dict.to_excel(writer, sheet_name='Descriptions', index_label='P3339_JL')
