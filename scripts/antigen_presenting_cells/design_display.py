import os
import numpy as np

from crisscross.core_functions.megastructures import Megastructure
from scripts.antigen_presenting_cells.capc_pattern_generator import capc_pattern_generator

design_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/CAPCs/version_1'
read_handles_from_file = True
np.random.seed(8)
########################################
# Preparing animation order for slats
# have to prepare these manually as the stagger is screwing up with the automatic detection system.
# The animation direction detector is also being turned off due to this issue.
# TODO: changing the direction of the slats so that they don't phase through other slats is still required for this kind of design.
custom_animation_dict = {}

groups = [['layer1-slat%s' % x for x in range(98, 114)],
          ['layer2-slat%s' % x for x in range(17, 33)],
          ['layer1-slat%s' % x for x in range(130, 156)],
          ['layer2-slat%s' % x for x in range(33, 49)],
          ['layer1-slat%s' % x for x in range(162, 177)],
          ['layer2-slat%s' % x for x in range(82, 98)],
          ['layer1-slat%s' % x for x in range(177, 194)],
          ['layer2-slat%s' % x for x in range(66, 82)],
          ['layer1-slat%s' % x for x in range(146, 162)],
          ['layer2-slat%s' % x for x in range(50, 67)],
          ['layer1-slat%s' % x for x in range(114, 130)],
          ['layer2-slat%s' % x for x in range(1, 17)],
          ]
for order, group in enumerate(groups):
    for slat in group:
        custom_animation_dict[slat] = order
########################################
# Actual megastructure
M1 = Megastructure(import_design_file=os.path.join(design_folder, 'basic_design.xlsx'))
M2 = Megastructure(import_design_file=os.path.join(design_folder, 'basic_design.xlsx'))

cargo_array_cd = capc_pattern_generator('central_dispersed', total_cd3_antigens=192, capc_length=66)
cargo_array_pd = capc_pattern_generator('peripheral_dispersed', total_cd3_antigens=192, capc_length=66)

M1.assign_cargo_handles_with_array(cargo_array_cd, cargo_key={1:'anti-CD3', 2:'anti-CD28'}, layer='top')
M2.assign_cargo_handles_with_array(cargo_array_pd, cargo_key={1:'anti-CD3', 2:'anti-CD28'}, layer='top')

M1.create_standard_graphical_report(os.path.join(design_folder, 'visualization/central'),
                                    colormap='Set1',
                                    cargo_colormap='Dark2',
                                    seed_color=(1.0, 1.0, 0.0))

M2.create_standard_graphical_report(os.path.join(design_folder, 'visualization/peripheral'),
                                    colormap='Set1',
                                    cargo_colormap='Dark2',
                                    seed_color=(1.0, 1.0, 0.0))

M1.create_blender_3D_view(os.path.join(design_folder, 'visualization/central'),
                          colormap='Set1',
                          cargo_colormap='Dark2',
                          animate_assembly=True,
                          seed_color=(1.0, 1.0, 0.0),
                          custom_assembly_groups=custom_animation_dict,
                          animation_type='translate',
                          camera_spin=True)

M2.create_blender_3D_view(os.path.join(design_folder, 'visualization/peripheral'),
                          colormap='Set1',
                          cargo_colormap='Dark2',
                          animate_assembly=True,
                          seed_color=(1.0, 1.0, 0.0),
                          custom_assembly_groups=custom_animation_dict,
                          animation_type='translate',
                          camera_spin=True)
