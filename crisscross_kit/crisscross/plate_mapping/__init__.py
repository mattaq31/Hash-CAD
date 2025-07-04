from crisscross.plate_mapping.plate_constants import (sanitize_plate_map, base_directory, slat_core, \
                                                      flat_staple_plate_folder, seed_plate_folder, crisscross_h5_handle_plates,
                                                      assembly_handle_plate_folder, crisscross_h2_handle_plates, \
                                                      seed_plug_plate_corner, seed_plug_plate_center,
                                                      seed_plug_plate_all, cargo_plate_folder,
                                                      nelson_quimby_antihandles,
                                                      octahedron_patterning_v1, slat_core_latest,
                                                      simpsons_mixplate_antihandles, seed_slat_purification_handles,
                                                      cckz_h5_handle_plates, cckz_h2_antihandle_plates,
                                                      cckz_h5_sample_handle_plates, cckz_h2_sample_antihandle_plates,
                                                      cnt_patterning, paint_h5_handles, seed_plug_plate_all_8064)
import os
import ast
from pydoc import locate

# This piece of code allows for easy importing of new plates by just specifying the class name as a string rather
# than a full explicit import.
available_plate_loaders = {}
functions_dir = os.path.join(base_directory, 'crisscross_kit', 'crisscross', 'plate_mapping')
for dirpath, _, filenames in os.walk(functions_dir):
    for file in filenames:
        if file.endswith('.py') and file not in ('.DS_Store', '__init__.py'):
            file_path = os.path.join(dirpath, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                p = ast.parse(f.read())
            classes = [node.name for node in ast.walk(p) if isinstance(node, ast.ClassDef)]

            # Convert full path to import path
            relative_path = os.path.relpath(file_path, base_directory)
            import_path = relative_path.replace(os.path.sep, '.').rsplit('.py', 1)[0]

            for _class in classes:
                available_plate_loaders[_class] = f"{import_path}.{_class}"

def get_plateclass(name, plate_name, plate_folder, **kwargs):
    """
    Main model extractor.
    :param name: Plate class name.
    :param plate_name: Name/s of selected plate file/s.
    :param plate_folder: Plate folder location
    :return: instantiated plate reader class.
    """
    return locate(available_plate_loaders[name])(plate_name, plate_folder, **kwargs)

def get_assembly_handle_v2_sample_plates():
    """
    Generates plates used for the initial testing of assembly handle library v2.
    """

    crisscross_antihandle_y_plates = get_plateclass('HashCadPlate',
                                                    cckz_h2_sample_antihandle_plates,
                                                    assembly_handle_plate_folder)

    crisscross_handle_x_plates = get_plateclass('HashCadPlate',
                                                cckz_h5_sample_handle_plates,
                                                assembly_handle_plate_folder)

    return crisscross_antihandle_y_plates, crisscross_handle_x_plates


def get_standard_plates(handle_library_v2=False):
    """
    Generates standard plates used commonly in most designs.
    """
    core_plate = get_plateclass('HashCadPlate', slat_core, flat_staple_plate_folder)

    if handle_library_v2:
        crisscross_antihandle_y_plates = get_plateclass('HashCadPlate',
                                                        cckz_h2_antihandle_plates,
                                                        assembly_handle_plate_folder)

        crisscross_handle_x_plates = get_plateclass('HashCadPlate',
                                                    cckz_h5_handle_plates,
                                                    assembly_handle_plate_folder)
    else:
        crisscross_antihandle_y_plates = get_plateclass('HashCadPlate',
                                                        crisscross_h5_handle_plates[3:] + crisscross_h2_handle_plates,
                                                        assembly_handle_plate_folder)

        crisscross_handle_x_plates = get_plateclass('HashCadPlate',
                                                    crisscross_h5_handle_plates[0:3],
                                                    assembly_handle_plate_folder)

    seed_plate = get_plateclass('HashCadPlate', seed_plug_plate_corner, seed_plate_folder)
    center_seed_plate = get_plateclass('HashCadPlate', seed_plug_plate_center, seed_plate_folder)
    combined_seed_plate = get_plateclass('HashCadPlate', seed_plug_plate_all, seed_plate_folder)
    all_8064_seed_plugs = get_plateclass('HashCadPlate', seed_plug_plate_all_8064, seed_plate_folder)
    return (core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate,
            combined_seed_plate, all_8064_seed_plugs)

def get_cutting_edge_plates(handle_library_working_stock_concentration=None):
    """
    Generates standard plates used commonly in most designs.  These are the most updated plates in the current library.
    """
    core_plate = get_plateclass('HashCadPlate', slat_core_latest, flat_staple_plate_folder)

    crisscross_antihandle_y_plates = get_plateclass('HashCadPlate',
                                                    cckz_h2_antihandle_plates,
                                                    assembly_handle_plate_folder,
                                                    apply_working_stock_concentration=handle_library_working_stock_concentration)

    crisscross_handle_x_plates = get_plateclass('HashCadPlate',
                                                cckz_h5_handle_plates,
                                                assembly_handle_plate_folder,
                                                apply_working_stock_concentration=handle_library_working_stock_concentration)

    all_8064_seed_plugs = get_plateclass('HashCadPlate', seed_plug_plate_all_8064, seed_plate_folder)

    return core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, all_8064_seed_plugs


def get_cargo_plates():
    """
    Generates standard cargo plates used commonly in most designs.
    """
    src_007 = get_plateclass('HashCadPlate', simpsons_mixplate_antihandles, cargo_plate_folder)
    src_005 = get_plateclass('HashCadPlate', nelson_quimby_antihandles, cargo_plate_folder)
    src_004 = get_plateclass('HashCadPlate', seed_slat_purification_handles, cargo_plate_folder)
    P3518 = get_plateclass('HashCadPlate', octahedron_patterning_v1, cargo_plate_folder)
    P3510 = get_plateclass('HashCadPlate', cnt_patterning, cargo_plate_folder)
    P3628 = get_plateclass('HashCadPlate', paint_h5_handles, cargo_plate_folder)
    return src_004, src_005, src_007, P3518, P3510, P3628
