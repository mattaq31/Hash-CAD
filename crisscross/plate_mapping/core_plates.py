from crisscross.plate_mapping import BasePlate
import math


class ControlPlate(BasePlate):
    """
    Core control plate containing slat sequences and flat (not jutting out) H2/H5 staples.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def identify_wells_and_sequences(self):
        for pattern, well, seq in zip(self.plates[0]['name'].str.extract(r'(\d+-h\d)', expand=False).tolist(),
                                      self.plates[0]['well'].tolist(), self.plates[0]['sequence'].tolist()):
            if isinstance(pattern, float) and math.isnan(pattern):
                continue
            key = (int(pattern.split('-')[0]), int(pattern.split('-')[1][1]), 0)
            if key[1] == 5:  # deals with continuation of IDs after 32 for h5 handles
                key = (key[0]-32, 5, 0)
            self.wells[key] = well
            self.sequences[key] = seq
