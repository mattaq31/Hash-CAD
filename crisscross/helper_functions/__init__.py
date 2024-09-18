import os
import pandas as pd

dna_complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}

def revcom(sequence):
    """
    Reverse complements a DNA sequence.
    :param sequence: DNA string, do not add any other characters (TODO: make more robust)
    :return: processed sequence (string)
    """
    return "".join(dna_complement[n] for n in reversed(sequence))


def create_dir_if_empty(*directories):
    """
    Creates a directory if it doesn't exist.
    :param directories: Single filepath or list of filepaths.
    :return: None
    """
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)


def index_converter(ind, images_per_row, double_indexing=True):
    """
    Converts a singe digit index into a double digit system, if required.
    :param ind: The input single index
    :param images_per_row: The number of images per row in the output figure
    :param double_indexing: Whether or not double indexing is required
    :return: Two split indices or a single index if double indexing not necessary
    """
    if double_indexing:
        return int(ind / images_per_row), ind % images_per_row  # converts indices to double
    else:
        return ind

def save_list_dict_to_file(output_folder, filename, lists_dict, selected_data=None, append=True):
    """
    Saves a dictionary of lists to a file. TODO: finish docstring
    :param output_folder:
    :param filename:
    :param lists_dict:
    :param selected_data:
    :param append:
    :return:
    """

    true_filename = os.path.join(output_folder, filename)

    pd_data = pd.DataFrame.from_dict(lists_dict)

    if selected_data is not None and os.path.isfile(true_filename):
        if type(selected_data) == int:
            selected_data = [selected_data]
        pd_data = pd_data.loc[selected_data]

    if not os.path.isfile(true_filename):  # if there is no file in place, no point in appending
        append = False

    pd_data.to_csv(true_filename, mode='a' if append else 'w', header=not append, index=False)

