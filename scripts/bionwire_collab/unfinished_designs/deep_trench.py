import os
import numpy as np

from crisscross.core_functions.megastructures import Megastructure

design_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/bionwire/basic_design'
read_handles_from_file = True
np.random.seed(8)

########################################
# Actual megastructure
M_DT = Megastructure(import_design_file=os.path.join(design_folder, 'bigger_structure.xlsx'))
# M_DT.create_standard_graphical_report(os.path.join(design_folder, 'deeper_trench'), colormap='Set1',
#                                       seed_color=(1.0, 1.0, 0.0))

M_DT.create_blender_3D_view(os.path.join(design_folder, 'deeper_trench'), colormap='Set1',
                            animate_assembly=False,
                            seed_color=(1.0, 1.0, 0.0),
                            camera_spin=True)

