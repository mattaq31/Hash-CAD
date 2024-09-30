import os
import numpy as np

from crisscross.core_functions.megastructures import Megastructure

design_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/bionwire/basic_design'
read_handles_from_file = True
np.random.seed(8)
########################################
# Preparing animation order for slats
# have to prepare these manually as the stagger is screwing up with the automatic detection system.
# The animation direction detector is also being turned off due to this issue.
# TODO: changing the direction of the slats so that they don't phase through other slats is still required for this kind of design.
custom_glider_animation_dict = {}

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

slat_flip_list = ['layer1-slat%s' % x for x in range(114, 130)]

for order, group in enumerate(groups):
    for slat in group:
        custom_glider_animation_dict[slat] = order
########################################
# Actual megastructure
M_DT = Megastructure(import_design_file=os.path.join(design_folder, 'double_trench.xlsx'))
M_X = Megastructure(import_design_file=os.path.join(design_folder, 'trench_x.xlsx'))
M_Y = Megastructure(import_design_file=os.path.join(design_folder, 'trench_y.xlsx'))

M_DT.create_standard_graphical_report(os.path.join(design_folder, 'Design_XY'), colormap='Set1',
                                      seed_color=(1.0, 1.0, 0.0))
M_X.create_standard_graphical_report(os.path.join(design_folder, 'Design_X'), colormap='Set1',
                                     seed_color=(1.0, 1.0, 0.0))
M_Y.create_standard_graphical_report(os.path.join(design_folder, 'Design_Y'), colormap='Set1',
                                     seed_color=(1.0, 1.0, 0.0))

M_DT.create_blender_3D_view(os.path.join(design_folder, 'Design_XY'), colormap='Set1',
                            animate_assembly=True,
                            seed_color=(1.0, 1.0, 0.0),
                            custom_assembly_groups=custom_glider_animation_dict,
                            correct_slat_entrance_direction=False,
                            animation_type='translate',
                            slat_flip_list=slat_flip_list,
                            camera_spin=True)
M_X.create_blender_3D_view(os.path.join(design_folder, 'Design_X'), colormap='Set1',
                           animate_assembly=True,
                           seed_color=(1.0, 1.0, 0.0),
                           custom_assembly_groups=custom_glider_animation_dict,
                           animation_type='translate',
                           correct_slat_entrance_direction=False,
                           slat_flip_list=slat_flip_list,
                           camera_spin=True)
M_Y.create_blender_3D_view(os.path.join(design_folder, 'Design_Y'), colormap='Set1',
                           animate_assembly=True,
                           seed_color=(1.0, 1.0, 0.0),
                           correct_slat_entrance_direction=False,
                           custom_assembly_groups=custom_glider_animation_dict,
                           animation_type='translate',
                           slat_flip_list=slat_flip_list,
                           camera_spin=True)
