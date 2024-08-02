from crisscross.plate_mapping import BasePlate
import math


class CornerSeedPlugPlate(BasePlate):
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


class CenterSeedPlugPlate(BasePlate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def identify_wells_and_sequences(self):
        position_tracker = 1
        for pattern, well, seq in zip(self.plates[0]['name'].tolist(),
                                      self.plates[0]['well'].tolist(), self.plates[0]['sequence'].tolist()):
            if 'Oligo' in pattern:
                continue
            key = (int(pattern.split('.')[0][1:]) + 1, 2, position_tracker)
            if key[0] == 18:
                position_tracker += 1
            self.wells[key] = well
            self.sequences[key] = seq


class CombinedSeedPlugPlate(BasePlate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def identify_wells_and_sequences(self):
        for pattern, well, seq in zip(self.plates[0]['name'].tolist(),
                                      self.plates[0]['well'].tolist(), self.plates[0]['sequence'].tolist()):

            name_key = pattern.split('_')
            key = (int(name_key[2].split('-')[1]), int(name_key[1][1]), int(name_key[0].split('-')[1]))
            self.wells[key] = well
            self.sequences[key] = seq
