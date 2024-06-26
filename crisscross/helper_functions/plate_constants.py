from itertools import product
from string import ascii_uppercase
import os
from os.path import join

plate96 = [x + str(y) for x, y in product(ascii_uppercase[:8], range(1, 12 + 1))]
plate384 = [x + str(y) for x, y in product(ascii_uppercase[:16], range(1, 24 + 1))]

base_directory = os.path.abspath(join(__file__, os.path.pardir, os.path.pardir, os.path.pardir))
core_plate_folder = join(base_directory, 'core_plates')
assembly_handle_folder = join(base_directory, 'assembly_handle_plates')
cargo_plate_folder = join(base_directory, 'cargo_plates')

crisscross_h5_handle_plates = ["P3247_SW_handles", "P3248_SW_handles", "P3249_SW_handles",
                               "P3250_SW_antihandles", "P3251_CW_antihandles",
                               "P3252_SW_antihandles"]  # first 3 are 'handle' plates, last 3 are 'anti-handle' plates

crisscross_h2_handle_plates = ["P3536_MA_h2_antihandles", "P3537_MA_h2_antihandles", "P3538_MA_h2_antihandles"]

# These have not been ordered in order to save on extra DNA expenses.
crisscross_not_ordered_h2_handle_plates = ["PX1_MA_h2_handles", "PX2_MA_h2_handles", "PX3_MA_h2_handles"]

seed_core = 'sw_src001_seedcore'  # this contains all the seed sequences, including the socket sequences
slat_core = 'sw_src002_slatcore'  # this contains all the slat sequences, including the control sequences (no handle)

seed_plug_plate_center = 'P2854_CW_seed_plug_center'  # this contains the H2 plug sequences to bind to the seed at the center of the x-slats
seed_plug_plate_corner = 'P3339_JL_seed_plug_corner'  # this contains another variation of H2 plug sequences - they go to the corner of a set of x-slats

nelson_quimby_antihandles = 'sw_src005_antiNelsonQuimby_cc6hb_h2handles'  # this contains the full set of h2 handles for antiNelson/Quimby extensions
h2_biotin_direct = 'P3510_SSW_biotin'  # this contains two core slat sequences with directly biotinylated H2 handles
octahedron_patterning_v1 = 'P3518_MA_octahedron_patterning_v1'  # this contains the H2 sequences for the octahedron patterning (diagonal) and H2/H5 strands for cross-bar binding
simpsons_mixplate_antihandles = 'sw_src007_nelson_quimby_bart_edna'  # this contains a variety of Bart, Edna, Nelson and Quimby handles for both H2 and H5

def sanitize_plate_map(name):
    """
    Actual plate name for the Echo always just features the person's name and the plate ID.
    :param name: Long-form plate name
    :return: Barebones plate name for Echo
    """
    return name.split('_')[0] + '_' + name.split('_')[1]
