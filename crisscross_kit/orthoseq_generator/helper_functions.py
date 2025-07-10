import signal
import os
import pickle
from datetime import datetime

# Default file name for the energy library
_precompute_library_filename = None

USE_LIBRARY = True




class DelayedKeyboardInterrupt:
    '''
    Context manager that delays KeyboardInterrupt (Ctrl+C) during critical operations, such as saving files.

    This prevents corruption of the precomputed energy library by ignoring interrupts until the file write is safely completed.
    '''
    
    def __enter__(self):
        self.signal_received = False
        self.old_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self.handler)

    def handler(self, sig, frame):
        print("\nDelayed KeyboardInterrupt until file writing is done...")
        self.signal_received = (sig, frame)

    def __exit__(self, type, value, traceback):
        signal.signal(signal.SIGINT, self.old_handler)
        if self.signal_received:
            self.old_handler(*self.signal_received)




def save_pickle_atomic(data, filepath):
    '''
    Saves a Python object to disk as a pickle file in a safe and atomic way.

    Input:
        - data: Python object to save (typically a dictionary).
        - filepath (str): Full path to the target pickle file.

    Notes:
        - Writes to a temporary file first and then moves it to the target path to avoid file corruption in case of crashes.
        - Creates the target folder if it does not exist yet.
    '''
    
    tmp_path = filepath + ".tmp"
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(tmp_path, "wb") as f:
        pickle.dump(data, f)

    # This safely replaces the original file with the completed tmp file
    os.replace(tmp_path, filepath)



def choose_precompute_library(filename):
    '''
    Sets the name of the precomputed energy library file.

    Input:
        - filename (str): Name of the pickle file where precomputed energies are or will be stored.

    Notes:
        - This updates the global variable used by other functions to locate the correct library.
    '''
    
    global _precompute_library_filename
    _precompute_library_filename = filename



def get_library_path():
    '''
    Returns the full file path to the currently selected precomputed energy library.

    Output:
        - str: Full path to the pickle file containing the precomputed Gibbs free energy dictionary.

    Notes:
        - Uses the global variable set by choose_precompute_library().
        - If no file name has been set, defaults to 'test_lib.pkl' in the 'pre_computed_energies' folder.
    '''
    
    folder = "pre_computed_energies"
    filename = _precompute_library_filename or "test_lib.pkl"
    return os.path.join(folder, filename)


def get_default_results_folder():
    '''
    Returns the default path to the 'results' folder where output files should be saved. This is the folder where the generated sequences end up. 

    Output:
        - str: Absolute path to the 'results' directory.

    Notes:
        - The folder is created automatically if it does not exist.
        - The path is always relative to the current working directory from which the script was executed (not the script's own location).
    '''
    
    base_dir = os.getcwd()  # Directory from which the script was executed
    folder_path = os.path.join(base_dir, "results")
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def save_sequence_pairs_to_txt(sequence_pairs, filename=None):
    '''
    Saves a list of DNA sequence pairs to a plain text file in the default results folder.

    Input:
        - sequence_pairs (list): List of (sequence, reverse_complement) tuples.
        - filename (str or None): Optional custom file name. If None, the name is generated based on timestamp and sequence length.

    Notes:
        - The file is saved in the 'results' folder created by get_default_results_folder().
        - The file contains two columns: sequence and reverse complement, separated by a tab.
        - Automatically generates an informative file name if none is provided.
    '''
    
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

def load_sequence_pairs_from_txt(filename):
    '''
    Loads DNA sequence pairs from a plain text file in the default results folder.

    Input:
        - filename (str): Name of the text file to load.

    Output:
        - list: List of (sequence, reverse_complement) tuples loaded from the file.

    Notes:
        - The file is expected to contain tab-separated values: sequence <TAB> reverse_complement.
        - If the file does not exist, raises a FileNotFoundError.
    '''
    
    folder_path = get_default_results_folder()
    full_path = os.path.join(folder_path, filename)

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