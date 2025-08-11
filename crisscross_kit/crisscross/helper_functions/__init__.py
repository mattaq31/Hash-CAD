import os
import zipfile
from itertools import product
from string import ascii_uppercase
import numpy as np
import pandas as pd
import re
from pathlib import Path

dna_complement = {'A': 'T', 'C': 'G', 'G': 'C', 'T': 'A'}


# attempts to isolate code package base directory location
_here = Path(__file__).resolve()

# Try dev mode repo root
dev_root = _here.parents[3]  # 3 pardirs from file
developer_mode_package = False
if (dev_root / "pyproject.toml").exists() or (dev_root / ".git").exists():
    base_directory = str(dev_root)
    developer_mode_package = True
else:
    # Installed mode: crisscross_kit is the package root
    base_directory = str(_here.parents[2])  # only 2 pardirs from __file__

plate96 = [x + str(y) for x, y in product(ascii_uppercase[:8], range(1, 12 + 1))]
plate384 = [x + str(y) for x, y in product(ascii_uppercase[:16], range(1, 24 + 1))]
plate96_center_pattern = [x + str(y) for x, y in product(ascii_uppercase[:8], range(3, 10 + 1))]

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
    :return: N/A
    """
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)


def clear_folder_contents(root_folder):
    """
    Deletes all files in selected folder.
    :param root_folder: Folder within which all files should be deleted.
    :return: N/A
    """
    for dirpath, dirnames, filenames in os.walk(root_folder, topdown=False):
        # Remove files
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            os.remove(file_path)


def zip_folder_to_disk(folder_path, output_zip_path):
    """
    Zips a folder into a zip file.
    :param folder_path: Location of the folder to be zipped.
    :param output_zip_path: New zip file location.
    :return: N/A
    """
    try:
        # Create a ZipFile object with the output path
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk the directory tree
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    # Create the full path to the file
                    file_path = os.path.join(root, file)
                    # Create a relative path inside the zip
                    arcname = os.path.relpath(file_path, folder_path)
                    # Write the file to the zip
                    zipf.write(file_path, arcname=arcname)
        print(f"ZIP file created successfully: {output_zip_path}")
    except Exception as e:
        print(f"An error occurred while zipping files: {e}")


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
    Saves a dictionary of lists to an excel file.
    :param output_folder: Folder to save final file
    :param filename: Name of the file to save
    :param lists_dict: Dictionary of lists.  Each key will become a column header, while the data will be saved in rows.
      Each list must have the same length.
    :param selected_data: Optional list of specific indices to save.  If None, all data will be saved.
    :param append: Set to true to append to an existing file if this is available.
    :return: N/A
    """

    true_filename = os.path.join(output_folder, filename)
    pd_data = pd.DataFrame.from_dict(lists_dict)

    if selected_data is not None and os.path.isfile(true_filename):  # only save specific rows instead of the whole list
        if type(selected_data) == int:
            selected_data = [selected_data]
        pd_data = pd_data.loc[selected_data]

    if not os.path.isfile(true_filename):  # if there is no file in place, no point in appending
        append = False

    pd_data.to_csv(true_filename, mode='a' if append else 'w', header=not append, index=False)


def convert_np_to_py(data):
    """
    Converts numpy data types to python data types.  Only works on integers, floats and ndarrays.
    :param data: Numpy data, dictionary of numpy data or list of numpy data
    :return: Updated data
    """
    if isinstance(data, dict):
        return {key: convert_np_to_py(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_np_to_py(element) for element in data]
    elif isinstance(data, np.integer):
        return int(data)
    elif isinstance(data, np.floating):
        return float(data)
    elif isinstance(data, np.ndarray):
        return data.tolist()
    else:
        return data

def natural_sort_key(key):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', key)]
