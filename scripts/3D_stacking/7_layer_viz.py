from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions.plate_constants import simpsons_mixplate_antihandles, cargo_plate_folder
from crisscross.plate_mapping import get_standard_plates, get_plateclass
import os


main_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/3D_stacking'
design_folder = os.path.join(main_folder, 'designs')
echo_folder = os.path.join(main_folder, 'echo_commands')
graphics_required = False

core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate = get_standard_plates()
simpsons_mixplate = get_plateclass('GenericPlate', simpsons_mixplate_antihandles, cargo_plate_folder)

M1 = Megastructure(import_design_file=os.path.join(design_folder, 'H26_design_with_7_layers.xlsx'))

# M1.create_standard_graphical_report(os.path.join(main_folder, 'H26_7_layers_viz'),
#                                     colormap='Set1',
#                                     cargo_colormap='Dark2',
#                                     seed_color=(1.0, 1.0, 0.0))

M1.create_blender_3D_view(os.path.join(main_folder, 'H26_7_layers_viz'), animate_assembly=False, animation_type='translate',
                               custom_assembly_groups=None, slat_translate_dict=None, minimum_slat_cutoff=15,
                               camera_spin=False, correct_slat_entrance_direction=True, colormap='Set1',
                               cargo_colormap='Dark2', slat_flip_list=None, seed_color=(1.0, 0.0, 0.0),
                               include_bottom_light=False)
