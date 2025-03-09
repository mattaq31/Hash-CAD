from crisscross.plate_mapping import BasePlate
from crisscross.plate_mapping.plate_constants import sanitize_plate_map
import math


class CrisscrossHandlePlates(BasePlate):
    """
    Mix of multiple plates containing all possible 32x32x2 combinations of crisscross handles.
    In this system, cargo ID = assembly handle ID.
    """
    def __init__(self, *args, plate_slat_sides, **kwargs):
        self.plate_mapping = {}
        self.plate_slat_sides = plate_slat_sides
        super().__init__(*args, **kwargs)

    def identify_wells_and_sequences(self):
        for plate, plate_name, plate_slat_side in zip(self.plates, self.plate_names, self.plate_slat_sides):
            for pattern, well, seq in zip(plate['description'].str.extract(r'(n\d+_k\d+)', expand=False).tolist(), plate['well'].tolist(), plate['sequence'].tolist()):
                if isinstance(pattern, float) and math.isnan(pattern):
                    continue
                key = (int(pattern.split('_k')[0][1:]) + 1, plate_slat_side, int(pattern.split('_k')[1]))
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
        if cargo_id == 0:
            raise RuntimeError('Cargo ID cannot be set to 0 or left blank for crisscross handle plates.')
        return sanitize_plate_map(self.plate_mapping[(slat_position, slat_side, cargo_id)])
