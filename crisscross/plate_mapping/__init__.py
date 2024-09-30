from crisscross.core_functions.plate_handling import read_dna_plate_mapping
from crisscross.helper_functions.plate_constants import (sanitize_plate_map, base_directory, slat_core, \
                                                         core_plate_folder, crisscross_h5_handle_plates,
                                                         assembly_handle_folder, crisscross_h2_handle_plates, \
                                                         seed_plug_plate_corner, seed_plug_plate_center,
                                                         seed_plug_plate_all, cargo_plate_folder,
                                                         nelson_quimby_antihandles,
                                                         octahedron_patterning_v1,
                                                         simpsons_mixplate_antihandles, seed_slat_purification_handles)
import os
import ast
from pydoc import locate
from collections import defaultdict


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


# This piece of code allows for easy importing of new plates by just specifying the class name as a string rather
# than a full explicit import.
available_plate_loaders = {}
functions_dir = os.path.join(base_directory, 'crisscross', 'plate_mapping')
for file in os.listdir(functions_dir):
    if file == '.DS_Store' or file == '__init__.py' or '.py' not in file:
        continue
    p = ast.parse(open(os.path.join(functions_dir, file), 'r').read())
    classes = [node.name for node in ast.walk(p) if isinstance(node, ast.ClassDef)]
    for _class in classes:
        available_plate_loaders[_class] = 'crisscross.plate_mapping.%s.%s' % (file.split('.py')[0], _class)


def get_plateclass(name, plate_name, plate_folder, **kwargs):
    """
    Main model extractor.
    :param name: Plate class name.
    :param plate_name: Name/s of selected plate file/s.
    :param plate_folder: Plate folder location
    :return: instantiated plate reader class.
    """
    return locate(available_plate_loaders[name])(plate_name, plate_folder, **kwargs)


def get_standard_plates():
    """
    Generates standard plates used commonly in most designs.
    """
    core_plate = get_plateclass('ControlPlate', slat_core, core_plate_folder)
    crisscross_antihandle_y_plates = get_plateclass('CrisscrossHandlePlates',
                                                    crisscross_h5_handle_plates[3:] + crisscross_h2_handle_plates,
                                                    assembly_handle_folder, plate_slat_sides=[5, 5, 5, 2, 2, 2])
    crisscross_handle_x_plates = get_plateclass('CrisscrossHandlePlates',
                                                crisscross_h5_handle_plates[0:3],
                                                assembly_handle_folder, plate_slat_sides=[5, 5, 5])

    seed_plate = get_plateclass('CornerSeedPlugPlate', seed_plug_plate_corner, core_plate_folder)
    center_seed_plate = get_plateclass('CenterSeedPlugPlate', seed_plug_plate_center, core_plate_folder)
    combined_seed_plate = get_plateclass('CombinedSeedPlugPlate', seed_plug_plate_all, core_plate_folder)

    return core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate


def get_cargo_plates():
    """
    Generates standard cargo plates used commonly in most designs.
    """
    src_007 = get_plateclass('GenericPlate', simpsons_mixplate_antihandles, cargo_plate_folder)
    src_005 = get_plateclass('GenericPlate', nelson_quimby_antihandles, cargo_plate_folder)
    src_004 = get_plateclass('HybridPlate', seed_slat_purification_handles, cargo_plate_folder)
    P3518 = get_plateclass('GenericPlate', octahedron_patterning_v1, cargo_plate_folder)

    return src_004, src_005, src_007, P3518
