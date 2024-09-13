from colorama import Fore

from crisscross.plate_mapping.cargo_plates import GenericPlate


class HybridPlate(GenericPlate):
    """
    A generic cargo plate system that can read in any plate file with the handle-position-cargo syntax
    defined in the top left cell.  ID numbers are assigned to cargo at run-time.
    """

    def __init__(self, *args, **kwargs):
        self.non_slat_wells = {}
        self.non_slat_sequences = {}
        super().__init__(*args, **kwargs)

    def identify_wells_and_sequences(self):
        for pattern, well, seq in zip(self.plates[0]['name'].tolist(),
                                      self.plates[0]['well'].tolist(),
                                      self.plates[0]['sequence'].tolist()):
            if '_' not in pattern:
                # these sequences are 'non-slat' staples i.e. those that don't have a handle-position-cargo syntax.
                # For now, we are simply collecting them separately, but eventually we might consider using these
                # for other functionalities (e.g. preparing an echo protocol for a seed)
                self.non_slat_wells[pattern] = well
                self.non_slat_sequences[pattern] = seq
                continue

            cargo = pattern.split('_')[self.name_encoding['name']]
            position_str = pattern.split('_')[self.name_encoding['position']]
            if '*' in pattern:  # skips wells marked with *s (could be an invalid position or some other issue)
                continue

            int_string = ''.join(ch for ch in position_str if ch.isdigit())
            key = (int(int_string), 5 if 'h5' in pattern else 2, cargo)

            self.wells[key] = well
            self.sequences[key] = seq
        if len(self.non_slat_sequences) > 0:
            print(Fore.BLUE + f'Info: Plate {self.plate_names[0]} contains non-slat staples.' + Fore.RESET)


    def get_sequence(self, slat_position, slat_side, cargo_id=0):
        if cargo_id == 0:
            raise RuntimeError('Cargo ID cannot be set to 0 or left blank for cargo plates.')

        return self.sequences[(slat_position, slat_side, cargo_id)]

    def get_well(self, slat_position, slat_side, cargo_id=0):
        if cargo_id == 0:
            raise RuntimeError('Cargo ID cannot be set to 0 or left blank for cargo plates.')
        return self.wells[(slat_position, slat_side, cargo_id)]
