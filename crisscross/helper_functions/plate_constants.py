from itertools import product
from string import ascii_uppercase
from os.path import join
from crisscross.helper_functions import base_directory

plate96 = [x + str(y) for x, y in product(ascii_uppercase[:8], range(1, 12 + 1))]
plate384 = [x + str(y) for x, y in product(ascii_uppercase[:16], range(1, 24 + 1))]
plate96_center_pattern = [x + str(y) for x, y in product(ascii_uppercase[:8], range(3, 10 + 1))]

core_plate_folder = join(base_directory, 'core_plates')
assembly_handle_folder = join(base_directory, 'assembly_handle_plates')
cargo_plate_folder = join(base_directory, 'cargo_plates')
old_format_cargo_plate_folder = join(cargo_plate_folder, 'old_format')

# ASSEMBLY HANDLE PLATES

# V1 - ORIGINAL
crisscross_h5_handle_plates = ["P3533_SW_handles", "P3534_SW_handles", "P3535_SW_handles",
                               "P3250_SW_antihandles", "P3251_CW_antihandles",
                               "P3252_SW_antihandles"]  # first 3 are 'handle' plates, last 3 are 'anti-handle' plates

# new plates now supersede these plates (but contain the same sequences)
crisscross_h5_outdated_handle_plates = ["P3247_SW_handles", "P3248_SW_handles", "P3249_SW_handles",
                                        "P3250_SW_antihandles", "P3251_CW_antihandles",
                                        "P3252_SW_antihandles"]  # first 3 are 'handle' plates, last 3 are 'anti-handle' plates

crisscross_h2_handle_plates = ["P3536_MA_h2_antihandles", "P3537_MA_h2_antihandles", "P3538_MA_h2_antihandles"]

# These have not been ordered in order to save on extra DNA expenses.
crisscross_not_ordered_h2_handle_plates = ["PX1_MA_h2_handles", "PX2_MA_h2_handles", "PX3_MA_h2_handles"]

# V2 - Katzi Seqs

cckz_h5_handle_plates = ['P3601_MA_H5_handles_S1A', 'P3602_MA_H5_handles_S1B', 'P3603_MA_H5_handles_S1C']
cckz_h2_antihandle_plates = ['P3604_MA_H2_antihandles_S1A', 'P3605_MA_H2_antihandles_S1B', 'P3606_MA_H2_antihandles_S1C']


# SEED, CORE AND CARGO PLATES

seed_core = 'sw_src001_seedcore'  # this contains all the seed sequences, including the socket sequences
slat_core = 'sw_src002_slatcore'  # this contains all the slat sequences, including the control sequences (no handle)

seed_slat_purification_handles = "sw_src004_polyAgridiron" # this contains toehold-polyA extensions on gridiron seed staples for attachment to polyT beads and toehold-3letter code sequences for slat attachment to beads

seed_plug_plate_center = 'P2854_CW_seed_plug_center'  # this contains the H2 plug sequences to bind to the seed at the center of the x-slats
seed_plug_plate_corner = 'P3339_JL_seed_plug_corner'  # this contains another variation of H2 plug sequences - they go to the corner of a set of x-slats
seed_plug_plate_all = 'P3555_SSW_combined_seeds'  # this contains both seeds in one plate with a human-readable placement system

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
