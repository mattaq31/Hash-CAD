from itertools import product
from string import ascii_uppercase
import os
from os.path import join


plate96 = [x + str(y) for x, y in product(ascii_uppercase[:8], range(1, 12 + 1))]
plate384 = [x + str(y) for x, y in product(ascii_uppercase[:16], range(1, 24 + 1))]

base_directory = os.path.abspath(join(__file__, os.path.pardir, os.path.pardir, os.path.pardir))
core_plate_folder = join(base_directory, 'core_plates')
cargo_plate_folder = join(base_directory, 'cargo_plates')

crisscross_handle_plates = ["P3247_SW_xslat_handles", "P3248_SW_xslat_handles", "P3249_SW_xslat_handles",
                            "P3250_SW_yslat_handles", "P3251_CW_yslat_handles", "P3252_SW_yslat_handles"]  # first 3 are 'handle' plates, last 3 are 'anti-handle' plates

seed_core = 'sw_src001_seedcore'  # this contains all the seed sequences, including the socket sequences
slat_core = 'sw_src002_slatcore'  # this contains all the slat sequences, including the control sequences (no handle)

seed_plug_plate_center = 'P2854_CW_seed_plug_center'  # this contains the H2 plug sequences to bind to the seed at the center of the x-slats
seed_plug_plate_corner = 'P3339_JL_seed_plug_corner' # this contains another variation of H2 plug sequences - they go to the corner of a set of x-slats

octahedron_patterning_v1 = 'P3518_MA_octahedron_patterning_v1'  # this contains the H2 sequences for the octahedron patterning (diagonal) and H2/H5 strands for cross-bar binding


def sanitize_plate_map(name):
    """
    Actual plate name for the Echo always just features the person's name and the plate ID.
    :param name: Long-form plate name
    :return: Barebones plate name for Echo
    """
    return name.split('_')[0] + '_' + name.split('_')[1]

