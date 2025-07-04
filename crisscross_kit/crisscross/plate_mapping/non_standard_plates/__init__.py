import os
from collections import defaultdict

from crisscross.core_functions.plate_handling import read_dna_plate_mapping
from crisscross.plate_mapping import sanitize_plate_map


class BasePlate:
    """
    Base class for plate readers.  The pattern used to identify the wells and sequences needs to be defined in a subclass.
    Once all data read in, access can be facilitated via a standard 3-element index of the slat position (1-32),
    the slat side (H2 or H5) and the cargo ID (which can vary according to the specific plate in question).
    """


    def __init__(self, plate_name, plate_folder, pre_read_plate_dfs=None, plate_style='2d_excel', plate_size=384,
                 delay_well_identification=False):

        if isinstance(plate_name, str):
            plate_name = [plate_name]

        self.plate_names = []
        self.plates = []
        self.plate_folder = plate_folder

        for index, plate in enumerate(plate_name):
            self.plate_names.append(plate)
            if pre_read_plate_dfs is not None:
                self.plates.append(pre_read_plate_dfs[index])
            else:
                self.plates.append(read_dna_plate_mapping(os.path.join(self.plate_folder, plate + '.xlsx'),
                                                          data_type=plate_style, plate_size=plate_size))

        self.wells = defaultdict(bool)
        self.sequences = defaultdict(bool)
        if not delay_well_identification:
            self.identify_wells_and_sequences()

    def identify_wells_and_sequences(self):
        raise NotImplementedError('This class is just a template - need to use one of the subclasses instead of this.')

    def get_sequence(self, slat_position, slat_side, cargo_id=0):
        return self.sequences[(slat_position, slat_side, cargo_id)]

    def get_well(self, slat_position, slat_side, cargo_id=0):
        return self.wells[(slat_position, slat_side, cargo_id)]

    def get_plate_name(self, *args):
        return sanitize_plate_map(self.plate_names[0])
