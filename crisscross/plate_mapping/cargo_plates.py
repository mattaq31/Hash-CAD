from crisscross.plate_mapping import BasePlate
import pandas as pd
import os


class GenericPlate(BasePlate):
    """
    A generic cargo plate system that can read in any plate file with the handle-position-cargo syntax
    defined in the top left cell.  ID numbers are assigned to cargo at run-time.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, delay_well_identification=True, **kwargs)

        # reads in the encoding format from the top left cell of the plate 'Names' sheet
        all_data = pd.ExcelFile(os.path.join(self.plate_folder, self.plate_names[0] + '.xlsx'))
        names = all_data.parse("Names", header=None)
        name_encoding = names.iloc[0, 0]
        self.name_encoding = {}
        for index, name in enumerate(name_encoding.split('_')):  # TODO: so the only advantage of this system is that the name/side/position can be interchanged?
            self.name_encoding[name] = index

        self.identify_wells_and_sequences()

    def identify_wells_and_sequences(self):
        for pattern, well, seq in zip(self.plates[0]['name'].tolist(),
                                      self.plates[0]['well'].tolist(),
                                      self.plates[0]['sequence'].tolist()):

            cargo = pattern.split('_')[self.name_encoding['name']]

            position_str = pattern.split('_')[self.name_encoding['position']]
            if '*' in pattern:  # skips wells marked with *s (could be an invalid position or some other issue)
                continue

            int_string = ''.join(ch for ch in position_str if ch.isdigit())
            #key = (int(int_string), 5 if 'h5' in pattern else 2, cargo)

            orientation_str = pattern.split('_')[self.name_encoding['side']]
            key = (int(int_string), int(orientation_str[-1]), cargo) # to accommodate non h2/h5 cargo

            self.wells[key] = well
            self.sequences[key] = seq

    def get_sequence(self, slat_position, slat_side, cargo_id=0):
        if cargo_id == 0:
            raise RuntimeError('Cargo ID cannot be set to 0 or left blank for cargo plates.')

        return self.sequences[(slat_position, slat_side, cargo_id)]

    def get_well(self, slat_position, slat_side, cargo_id=0):
        if cargo_id == 0:
            raise RuntimeError('Cargo ID cannot be set to 0 or left blank for cargo plates.')
        return self.wells[(slat_position, slat_side, cargo_id)]
