import numpy as np

# the distance between slat handle points is 14nm.  For simplicity, this distance is set to 1 throughout the code.
# Given this, all other distances need to be scaled accordingly.

grid_y_60 = 0.5  # the 60deg grid system does not have an equal distance between each y and x position since each slat
                 # handle position is in a zig-zag pattern.
                 # The y and x need to be rescaled for each plot produced to match this system.

connection_angles = {
    '90': (1, 1),
    '60': (np.sqrt((1 ** 2) - (grid_y_60 ** 2)), grid_y_60)
}

slat_width = 10/14  # the width of a slat (six-helix bundle) is assumed to be 10nm
