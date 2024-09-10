import os
import numpy as np

from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.slats import Slat

design_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/bionwire/basic_design'
read_handles_from_file = True
np.random.seed(8)

########################################
# Actual megastructure
M_DT = Megastructure(import_design_file=os.path.join(design_folder, 'crossbar_example.xlsx'))


for i in range(10):
    pos1 = [12+(2*i), 29]
    pos2 = [pos1[0] + 24, pos1[1] + 18]
    new_slat = Slat(f'crossbar_slat_layer_3_{i+1}', 3, {1:pos1, 32:pos2})
    M_DT.slats[f'crossbar_slat_layer_3_{i+1}'] = new_slat

for i in range(10):
    pos1 = [18, 22 + (2*i)]
    pos2 = [pos1[0] + 18, pos1[1] + 24]
    new_slat = Slat(f'crossbar_slat_layer_0_{i+1}', 0, {1:pos1, 32:pos2})
    M_DT.slats[f'crossbar_slat_layer_0_{i+1}'] = new_slat

M_DT.create_standard_graphical_report(os.path.join(design_folder, 'crossbar_example'), colormap='Set1',
                                      seed_color=(1.0, 1.0, 0.0))

M_DT.create_blender_3D_view(os.path.join(design_folder, 'crossbar_example'), colormap='Set1',
                            animate_assembly=False,
                            seed_color=(1.0, 1.0, 0.0),
                            camera_spin=False)


