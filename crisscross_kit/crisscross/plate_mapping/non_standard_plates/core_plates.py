from crisscross.plate_mapping.non_standard_plates import BasePlate
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


class ControlPlateWithDuplicates(BasePlate):
    """
    Core control plate containing slat sequences and flat (not jutting out) H2/H5 staples.
    This format allows for duplicated source wells, which should help combat Echo errors.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def identify_wells_and_sequences(self):
        for pattern, well, seq in zip(self.plates[0]['name'].tolist(),
                                      self.plates[0]['well'].tolist(),
                                      self.plates[0]['sequence'].tolist()):
            key = (int(pattern.split('pos')[-1]), int(pattern.split('_')[1][1]), 0)
            if key in self.wells:
                self.wells[key].append(well)
            else:
                self.wells[key] = [well]
                self.sequences[key] = seq

    def get_well(self, slat_position, slat_side, cargo_id=0):
        return '{' + ';'.join(self.wells[(slat_position, slat_side, cargo_id)]) + '}'
