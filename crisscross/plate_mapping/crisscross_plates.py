from crisscross.plate_mapping import BasePlate
from crisscross.helper_functions.plate_constants import sanitize_plate_map
import math


class CrisscrossHandlePlates(BasePlate):
    """
    Mix of multiple plates containing all possible 32x32 combinations of crisscross handles.
    """
    def __init__(self, *args, **kwargs):
        self.plate_mapping = {}
        super().__init__(*args, **kwargs)

    def identify_wells_and_sequences(self):
        for plate, plate_name in zip(self.plates, self.plate_names):
            for pattern, well, seq in zip(plate['description'].str.extract(r'(n\d+_k\d+)', expand=False).tolist(), plate['well'].tolist(), plate['sequence'].tolist()):
                if isinstance(pattern, float) and math.isnan(pattern):
                    continue
                key = (int(pattern.split('_k')[0][1:]) + 1, 5, int(pattern.split('_k')[1]))
                self.wells[key] = well
                self.sequences[key] = seq
                self.plate_mapping[key] = plate_name

    def get_well(self, slat_position, slat_side, cargo_id=0):
        if cargo_id == 0:
            raise RuntimeError('Cargo ID cannot be set to 0 or left blank for crisscross handle plates.')
        return super().get_well(slat_position, slat_side, cargo_id)

    def get_sequence(self, slat_position, slat_side, cargo_id=0):
        if cargo_id == 0:
            raise RuntimeError('Cargo ID cannot be set to 0 or left blank for crisscross handle plates.')
        return super().get_sequence(slat_position, slat_side, cargo_id)

    def get_plate_name(self, slat_position, slat_side, cargo_id):
        return sanitize_plate_map(self.plate_mapping[(slat_position, slat_side, cargo_id)])
