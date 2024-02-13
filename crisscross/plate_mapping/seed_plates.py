from crisscross.plate_mapping import BasePlate
import math


class SeedPlugPlate(BasePlate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def identify_wells_and_sequences(self):
        for pattern, well, seq in zip(self.plates[0]['description'].str.extract(r'(x-\d+-n\d+)', expand=False).tolist(),
                                      self.plates[0]['well'].tolist(), self.plates[0]['sequence'].tolist()):
            if isinstance(pattern, float) and math.isnan(pattern):
                continue
            key = (int(pattern.split('-')[2][1:]) + 1, 2, int(pattern.split('-')[1]))
            self.wells[key] = well
            self.sequences[key] = seq
