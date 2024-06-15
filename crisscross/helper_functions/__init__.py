import os

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
