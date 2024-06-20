from crisscross.plate_mapping import BasePlate
import math


class OctahedronPlate(BasePlate):
    """
    Cargo plate created in February 2024 for an octahedron placement system (collab with Oleg Gang's group)
    """
    def __init__(self, *args, **kwargs):
        self.cargo_key = {
            'Homer': 4,
            'Krusty': 5,
            'Lisa': 6,
            'Marge': 7,
            'Patty': 8,
            'Quimby': 9,
            'Smithers': 10
        }
        super().__init__(*args, **kwargs)

    def identify_wells_and_sequences(self):
        for pattern, well, seq in zip(self.plates[0]['name'].tolist(),
                                      self.plates[0]['well'].tolist(), self.plates[0]['sequence'].tolist()):
            if 'antiBart' in pattern:
                cargo = 1
            elif 'antiEdna' in pattern:
                cargo = 2
            elif 'anti' in pattern:
                cargo = self.cargo_key[pattern.split('_h')[0].split('anti')[-1]]
            elif pattern == 'biotin_anchor':
                cargo = -1
            else:
                cargo = self.cargo_key[pattern.split('_h')[0].split('mer-')[-1]] + 7

            key = (int(pattern.split('_cargo_handle_')[-1]) if 'cargo_handle' in pattern else -1, 2 if '_h2_' in pattern else 5, cargo)

            self.wells[key] = well
            self.sequences[key] = seq


class AntiNelsonQuimbyPlate(BasePlate):
    """
    Cargo plate (sw_src005) created by Stella containing Nelson and Quimby antiHandles for all 32 slat positions.
    """
    def __init__(self, *args, **kwargs):
        self.cargo_key = {
            3: 'Nelson',
            4: 'Quimby'
        }
        super().__init__(*args, **kwargs)

    def identify_wells_and_sequences(self):
        for pattern, well, seq in zip(self.plates[0]['name'].tolist(),
                                      self.plates[0]['well'].tolist(), self.plates[0]['sequence'].tolist()):
            if 'Nelson' in pattern:
                cargo = 'Nelson'
            elif 'Quimby' in pattern:
                cargo = 'Quimby'
            else:  # everything else is unrelated and should be skipped (at least for now)
                continue

            key = (int(pattern.split('pos')[-1].split('-')[0]), 2, cargo)

            self.wells[key] = well
            self.sequences[key] = seq

    def get_sequence(self, slat_position, slat_side, cargo_id=0):
        return self.sequences[(slat_position, slat_side, self.cargo_key[cargo_id])]

    def get_well(self, slat_position, slat_side, cargo_id=0):
        return self.wells[(slat_position, slat_side, self.cargo_key[cargo_id])]


class H5AntiBartEdnaPlate(BasePlate):
    """
    Cargo plate (FILL IN NAME) containing Bart and Edna antiHandles for all 32 H5 slat positions.
    """
    def __init__(self, *args, **kwargs):
        self.cargo_key = {
            1: 'Bart',
            2: 'Edna'
        }
        super().__init__(*args, **kwargs)

    def identify_wells_and_sequences(self):
        for pattern, well, seq in zip(self.plates[0]['name'].tolist(),
                                      self.plates[0]['well'].tolist(), self.plates[0]['sequence'].tolist()):
            if 'Bart' in pattern:
                cargo = 'Bart'
            elif 'Edna' in pattern:
                cargo = 'Edna'
            else:
                raise RuntimeError('The plate file does not match the expected pattern for this plate.')

            key = (int(pattern.split('position_')[-1]), 5, cargo)

            self.wells[key] = well
            self.sequences[key] = seq

    def get_sequence(self, slat_position, slat_side, cargo_id=0):
        return self.sequences[(slat_position, slat_side, self.cargo_key[cargo_id])]

    def get_well(self, slat_position, slat_side, cargo_id=0):
        return self.wells[(slat_position, slat_side, self.cargo_key[cargo_id])]


class DirectBiotinPlate(BasePlate):
    """
    Cargo plate (P3510_SSW) created by Stella containing various DNA paint handles (Fribourg collab)
    and two additional H2 poly-T handles with biotin directly attached.
    """
    def __init__(self, *args, **kwargs):
        self.cargo_key = {
            3: 'biotin',
        }
        super().__init__(*args, **kwargs, plate_style='IDT_order')

    def identify_wells_and_sequences(self):
        for pattern, well, seq in zip(self.plates[0]['name'].tolist(),
                                      self.plates[0]['well'].tolist(), self.plates[0]['sequence'].tolist()):
            if isinstance(pattern, float) and math.isnan(pattern):
                continue
            if 'Biotin' in pattern:
                key = (int(pattern.split('pos')[-1].split('-')[0]), 2, 'biotin')
            else:  # everything else is unrelated and should be skipped (at least for now)
                continue

            self.wells[key] = well
            self.sequences[key] = seq

    def get_sequence(self, slat_position, slat_side, cargo_id=0):
        return self.sequences[(slat_position, slat_side, self.cargo_key[cargo_id])]

    def get_well(self, slat_position, slat_side, cargo_id=0):
        return self.wells[(slat_position, slat_side, self.cargo_key[cargo_id])]
