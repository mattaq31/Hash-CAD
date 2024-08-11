import numpy as np
import os

from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.slat_design import generate_standard_square_slats, generate_patterned_square_cco
from crisscross.core_functions.hamming_functions import generate_random_slat_handles

########################################
# script setup
np.random.seed(8)
########################################
# cargo prep
cargo_pattern = generate_patterned_square_cco('diagonal_octahedron_top_corner')
cargo_key = {1: 'antiBart', 2: 'antiEdna'}
########################################

########################################
# Shape generation and crisscross handle optimisation
slat_array, unique_slats_per_layer = generate_standard_square_slats(32)  # standard square
handle_array = generate_random_slat_handles(slat_array, 32)
########################################
# preparing seed placement (assumed to be center of megastructure)
insertion_seed_array = np.arange(16) + 1
insertion_seed_array = np.pad(insertion_seed_array[:, np.newaxis], ((0, 0), (4, 0)), mode='edge')

center_seed_array = np.zeros((32, 32))
center_seed_array[8:24, 13:18] = insertion_seed_array
########################################
# Actual megastructure
M1 = Megastructure(slat_array)
M1.assign_crisscross_handles(handle_array)
M1.assign_seed_handles(center_seed_array)
M1.assign_cargo_handles_with_array(cargo_pattern, cargo_key=cargo_key)

M1.create_standard_graphical_report(os.path.join('/Users/matt/Desktop', 'Design Graphics'), colormap='Set1',
                                    cargo_colormap=['#FFFF00', '#66ff00'], seed_color=(1.0, 0.0, 0.0))

M1.create_blender_3D_view('/Users/matt/Desktop', colormap='Set1',
                          cargo_colormap=['#FFFF00', '#66ff00'],
                          animate_assembly=True,
                          animation_type='translate',
                          camera_spin=False)
