import os
from datetime import datetime

ENERGY_TYPE = "total"
NUPACK_PARAMS = {
    "MATERIAL": "dna",
    "CELSIUS": 37,
    "SODIUM": 0.05,
    "MAGNESIUM": 0.025
}

def set_nupack_params(material="dna", celsius=37, sodium=0.05, magnesium=0.025):
    """
    Updates global NUPACK parameters used for all energy computations.

    Notes
    -----
    These values are read by functions in `sequence_computations` when building
    a NUPACK `Model`.

    :param material: NUPACK material type (e.g., "dna").
    :type material: str

    :param celsius: Temperature in Celsius.
    :type celsius: float

    :param sodium: Sodium concentration in M.
    :type sodium: float

    :param magnesium: Magnesium concentration in M.
    :type magnesium: float

    :returns: None
    :rtype: None
    """
    NUPACK_PARAMS["MATERIAL"] = material
    NUPACK_PARAMS["CELSIUS"] = celsius
    NUPACK_PARAMS["SODIUM"] = sodium
    NUPACK_PARAMS["MAGNESIUM"] = magnesium
def get_default_results_folder():

    """
    Returns the default path to the 'noflank_results' folder where output files containing the generated sequence pairs are saved.

    Description
    -----------
    The noflank_results directory is created automatically if it does not exist.
    The path is based on the current working directory from which the script was executed.
    

    :returns: Absolute path to the 'noflank_results' directory.
    :rtype: str
    """
    
    
    base_dir = os.getcwd()  # Directory from which the script was executed
    folder_path = os.path.join(base_dir, "noflank_results")
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def save_sequence_pairs_to_txt(sequence_pairs, filename=None):
    """
    Saves a list of DNA sequence pairs to a plain text file in the default noflank_results folder.

    Description
    -----------
    Each line in the output file contains a sequence and its reverse complement,
    separated by a tab. If `filename` is not provided, an informative name is
    generated based on the number of sequences, sequence length, and current timestamp.

    :param sequence_pairs: List of (sequence, reverse_complement) tuples.
    :type sequence_pairs: list of tuple

    :param filename: Optional custom file name. If None, a name is generated based
                     on timestamp and sequence length.
    :type filename: str or None

    :returns: None
    :rtype: None
    """
    
    if not sequence_pairs:
        print("No sequences to save.")
        return

    folder_path = get_default_results_folder()

    if filename is None:
        seq_length = len(sequence_pairs[0][0])
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"{len(sequence_pairs)}seq_{seq_length}bp_{timestamp}.txt"

    full_path = os.path.join(folder_path, filename)

    with open(full_path, "w") as f:
        for seq, rc_seq in sequence_pairs:
            f.write(f"{seq}\t{rc_seq}\n")

    print(f"Saved {len(sequence_pairs)} sequence pairs to:\n{full_path}")

def load_sequence_pairs_from_txt(filename,use_default_results_folder=True):
    """
    Loads DNA sequence pairs from a plain text file in the default noflank_results folder.

    Description
    -----------
    Reads a tab-separated text file where each line contains a sequence and its
    reverse complement. The file is located in the noflank_results directory returned by
    `get_default_results_folder()`.

    :param filename: Name of the text file to load.
    :type filename: str

    :param use_default_results_folder: If True, interpret `filename` relative to the
                                       default noflank_results folder; otherwise treat it as
                                       an absolute or relative path.
    :type use_default_results_folder: bool

    :returns: List of (sequence, reverse_complement) tuples loaded from the file.
    :rtype: list of tuple

    :raises FileNotFoundError: If the specified file does not exist.
    """
    if use_default_results_folder:
        folder_path = get_default_results_folder()
        full_path = os.path.join(folder_path, filename)
    else:
        full_path = filename

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"No such file: {full_path}")

    sequence_pairs = []
    with open(full_path, "r") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 2:
                sequence_pairs.append((parts[0], parts[1]))

    print(f"Loaded {len(sequence_pairs)} sequence pairs from:\n{full_path}")
    return sequence_pairs
