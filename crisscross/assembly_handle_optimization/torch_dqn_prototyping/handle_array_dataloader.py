from torch.utils.data import Dataset
import pandas as pd
import numpy as np
import os
from python_calamine import CalamineWorkbook
from crisscross.assembly_handle_optimization.hamming_compute import oneshot_hamming_compute, extract_handle_dicts


class HandleArrayDataset(Dataset):
    def __init__(self, base_folder, slat_array, slat_length=32, evo_cutoff=2000):
        self.base_folder = base_folder
        self.all_arrays = []
        self.slat_array = slat_array
        self.slat_length = slat_length
        for dirpath, dirnames, filenames in os.walk(base_folder):
            for file in filenames:
                if '.xlsx' in file and '$' not in file and int(file.split('_')[-1].split('.')[0]) <=evo_cutoff:

                    handle_array = np.array(pd.read_excel(os.path.join(dirpath, file), sheet_name='handle_interface_1',
                                                          header=None, engine='calamine'))
                    self.all_arrays.append(handle_array)

    def __len__(self):
        return len(self.all_arrays)

    def __getitem__(self, idx):

        handle_dict, antihandle_dict = extract_handle_dicts(np.expand_dims(self.all_arrays[idx], axis=-1), self.slat_array)
        real_hamming = oneshot_hamming_compute(handle_dict, antihandle_dict, self.slat_length)
        physics_score = np.average(np.exp(-10 * (real_hamming - 32)))
        log_physics_score = np.log10(physics_score).astype(np.float32)
        hamming_score = np.min(real_hamming)

        return {'handle_array': np.expand_dims(self.all_arrays[idx], axis=0),
                'hamming': hamming_score,
                'physics_score': physics_score,
                'log_physics_score': log_physics_score}
