from crisscross.plate_mapping import get_plateclass
from crisscross.core_functions.plate_handling import read_dna_plate_mapping
from crisscross.plate_mapping.plate_constants import cckz_h5_handle_plates, cckz_h2_antihandle_plates, assembly_handle_plate_folder, seed_plate_folder, cargo_plate_folder, flat_staple_plate_folder
from crisscross.plate_mapping import sanitize_plate_map

from collections import defaultdict
import os
from colorama import Fore


class HashCadPlate:
    """
    A standardized plate system that defines the same ID pattern for all possible handle types (cargo, assembly, seed, etc.).
    This same system can be read into #-CAD directly.
    Each plate also features a 2D layout tab to help visualize in the lab.
    """

    def __init__(self, plate_name, plate_folder, pre_read_plate_dfs=None, plate_size=384, apply_working_stock_concentration=None):

        self.concentrations = defaultdict(bool)
        self.wells = defaultdict(bool)
        self.sequences = defaultdict(bool)

        if isinstance(plate_name, str):
            plate_name = [plate_name]

        self.plate_names = []
        self.plates = []
        self.plate_folder = plate_folder
        self.plate_mapping = {}

        # allows for reading in multiple plates in the same instance
        for index, plate in enumerate(plate_name):
            self.plate_names.append(plate)
            if pre_read_plate_dfs is not None:
                self.plates.append(pre_read_plate_dfs[index])
            else:
                self.plates.append(read_dna_plate_mapping(os.path.join(self.plate_folder, plate + '.xlsx'), data_type='#-CAD', plate_size=plate_size))

        if apply_working_stock_concentration is not None:
            for p in self.plates:
                p['concentration'] = apply_working_stock_concentration

        self.identify_wells_and_sequences()

    def identify_wells_and_sequences(self):
        """
        Identifies wells and sequences from the plate data and combines them into one database.
        """
        assembly_handle_statement_made = None
        for plate, plate_name in zip(self.plates, self.plate_names):
            for row in plate.itertuples(index=False):
                pattern = row.name
                if pattern == 'NON-SLAT OLIGO' or not isinstance(pattern, str): # ignored or empty wells
                    continue
    
                well = row.well
                seq = row.sequence
                conc = row.concentration

                category, id, orientation_str, position_str = pattern.split('-')

                position = int(position_str.split('_')[1])  # e.g., 'position_1' -> '1'
                orientation = int(orientation_str[-1])

                if 'ASSEMBLY' in category:
                    version = category.split('_')[-1]  # e.g., 'ASSEMBLY_HANDLE_v2' -> 'v2'
                    category = category.split('_v')[0]  # e.g., 'ASSEMBLY_HANDLE_v2' -> 'ASSEMBLY'
                    if assembly_handle_statement_made is None:
                        # add color to the statement
                        print(Fore.GREEN + f'Using assembly handle library {version} for plates {self.plate_names}.' + Fore.RESET)
                        assembly_handle_statement_made = version
                    elif assembly_handle_statement_made != version:
                        raise RuntimeError(f'Assembly handle library version mismatch: {assembly_handle_statement_made} vs {version}.')
                # e.g., 'h2' -> '2'
                key = (category, position, orientation, id) # to accommodate non h2/h5 cargo

                if key in self.wells:
                    self.wells[key].append(well)
                else:
                    self.wells[key] = [well]
                    self.sequences[key] = seq
                    self.concentrations[key] = conc
                    self.plate_mapping[key] = plate_name

    def get_sequence(self, category, slat_position, slat_side, cargo_id=0):
        """
        To retrieve data from the database, the following keys are required:
        - category: 'cargo', 'assembly', 'seed', etc.
        - slat_position: physical slat handle ID i.e. 1, 2, ..., 32
        - slat_side: i.e. 2, 5 (for h2/h5 handles)
        - cargo_id: e.g., 'A', 'B', ..., 'Z' (for cargo plates) or 1-64 for assembly handles
        """
        return self.sequences[(category, slat_position, slat_side, cargo_id)]

    def get_well(self, category, slat_position, slat_side, cargo_id=0):
        """
        To retrieve data from the database, the following keys are required:
        - category: 'cargo', 'assembly', 'seed', etc.
        - slat_position: physical slat handle ID i.e. 1, 2, ..., 32
        - slat_side: i.e. 2, 5 (for h2/h5 handles)
        - cargo_id: e.g., 'A', 'B', ..., 'Z' (for cargo plates) or 1-64 for assembly handles
        """
        if len(self.wells[(category, slat_position, slat_side, cargo_id)]) > 1:
            return '{' + ';'.join(self.wells[(category, slat_position, slat_side, cargo_id)]) + '}'
        else:
            return self.wells[(category, slat_position, slat_side, cargo_id)][0]

    def get_concentration(self, category, slat_position, slat_side, cargo_id=0):
        """
        To retrieve data from the database, the following keys are required:
        - category: 'cargo', 'assembly', 'seed', etc.
        - slat_position: physical slat handle ID i.e. 1, 2, ..., 32
        - slat_side: i.e. 2, 5 (for h2/h5 handles)
        - cargo_id: e.g., 'A', 'B', ..., 'Z' (for cargo plates) or 1-64 for assembly handles
        """
        return self.concentrations[(category, slat_position, slat_side, cargo_id)]

    def get_plate_name(self, category, slat_position, slat_side, cargo_id):
        """
        To retrieve data from the database, the following keys are required:
        - category: 'cargo', 'assembly', 'seed', etc.
        - slat_position: physical slat handle ID i.e. 1, 2, ..., 32
        - slat_side: i.e. 2, 5 (for h2/h5 handles)
        - cargo_id: e.g., 'A', 'B', ..., 'Z' (for cargo plates) or 1-64 for assembly handles
        """
        return sanitize_plate_map(self.plate_mapping[(category, slat_position, slat_side, cargo_id)])


if __name__ == "__main__":
    # testing example plates
    plate = get_plateclass('HashCadPlate', 'P3643_MA_combined_seeds_8064',seed_plate_folder)
    plate_2 = get_plateclass('HashCadPlate', 'sw_src009_control_max', flat_staple_plate_folder)
    plate_3 = get_plateclass('HashCadPlate', 'sw_src007_nelson_quimby_bart_edna', cargo_plate_folder)
    assembly_handles = crisscross_handle_x_plates = get_plateclass('HashCadPlate', cckz_h5_handle_plates, assembly_handle_plate_folder)
    mixed_handles = get_plateclass('HashCadPlate', [cckz_h5_handle_plates[0], cckz_h2_antihandle_plates[0]], assembly_handle_plate_folder)
