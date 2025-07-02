import signal
import os
import pickle
from datetime import datetime

# Default file name for the energy library
_precompute_library_filename = None

USE_LIBRARY = True



# Keyboard Interrupt that protects the saving of the precompute Library to prevent corruption of the precompute library file
class DelayedKeyboardInterrupt:
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



# Saves a pkl file.
# This will create a pre_compute_energies folder in your working directory if it does not exist yet
# saves first to a temporary file and then copies it. This prevents file corruption if the program crashes. 
def save_pickle_atomic(data, filepath):
    tmp_path = filepath + ".tmp"
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(tmp_path, "wb") as f:
        pickle.dump(data, f)

    # This safely replaces the original file with the completed tmp file
    os.replace(tmp_path, filepath)


# Set the name of the energy library file.
def choose_precompute_library(filename):
    global _precompute_library_filename
    _precompute_library_filename = filename


# Helper function that returns the file path to the precomputed energy library.
# This path points to a pickle file containing a dictionary of previously calculated Gibbs free energies.
# The file name is recovered from a global variable. If the variable is None it will use the default dictionary
def get_library_path():
    folder = "pre_computed_energies"
    filename = _precompute_library_filename or "interactions_matrix_7mer.pkl"
    return os.path.join(folder, filename)


def get_default_results_folder():
    base_dir = os.getcwd()  # Directory from which the script was executed
    folder_path = os.path.join(base_dir, "results")
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def save_sequence_pairs_to_txt(sequence_pairs, filename=None):
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