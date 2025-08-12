from os.path import join
from crisscross.helper_functions import base_directory

# folder locations
flat_staple_plate_folder = join(base_directory, 'crisscross','dna_source_plates', 'flat_staple_plates')
assembly_handle_plate_folder = join(base_directory, 'crisscross','dna_source_plates', 'assembly_plates')
cargo_plate_folder = join(base_directory,  'crisscross','dna_source_plates', 'cargo_plates')
seed_plate_folder = join(base_directory,  'crisscross','dna_source_plates', 'seed_plates')

# old format plate locations
old_format_plate_folder = join(base_directory, 'crisscross','dna_source_plates', 'old_plate_format')
old_core_folder = join(old_format_plate_folder, 'core_plates')
old_cargo_folder = join(old_format_plate_folder, 'cargo_plates')
old_assembly_folder = join(old_format_plate_folder, 'assembly_handle_plates')

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

cckz_h5_sample_handle_plates = ['P3601_MA_H5_handles_S1A', 'P3602_MA_H5_handles_S1B', 'P3603_MA_H5_handles_S1C']
cckz_h2_sample_antihandle_plates = ['P3604_MA_H2_antihandles_S1A', 'P3605_MA_H2_antihandles_S1B', 'P3606_MA_H2_antihandles_S1C']

cckz_h5_handle_plates = ['P3649_MA_H5_handles_S1A', 'P3650_MA_H5_handles_S1B', 'P3651_MA_H5_handles_S1C', 'P3652_MA_H5_handles_S2A', 'P3653_MA_H5_handles_S2B', 'P3654_MA_H5_handles_S2C']
cckz_h2_antihandle_plates = ['P3655_MA_H2_antihandles_S1A', 'P3656_MA_H2_antihandles_S1B', 'P3657_MA_H2_antihandles_S1C', 'P3658_MA_H2_antihandles_S2A', 'P3659_MA_H2_antihandles_S2B', 'P3660_MA_H2_antihandles_S2C']


# SEED, CORE AND CARGO PLATES

seed_core = 'sw_src001_seedcore'  # this contains all the seed sequences, including the socket sequences
slat_core = 'sw_src002_slatcore'  # this contains all the slat sequences, including the control sequences (no handle)
slat_core_latest = 'sw_src009_control_max'  # this contains the slat control sequences with 4 duplicates per staple to reduce echo errors

seed_slat_purification_handles = "sw_src004_polyAgridiron" # this contains toehold-polyA extensions on gridiron seed staples for attachment to polyT beads and toehold-3letter code sequences for slat attachment to beads

seed_plug_plate_center = 'P2854_CW_seed_plug_center'  # this contains the H2 plug sequences to bind to the seed at the center of the x-slats
seed_plug_plate_corner = 'P3339_JL_seed_plug_corner'  # this contains another variation of H2 plug sequences - they go to the corner of a set of x-slats
seed_plug_plate_all = 'P3555_SSW_combined_seeds'  # this contains both seeds in one plate with a human-readable placement system
seed_plug_plate_center_8064 = 'P3621_SSW_seed_plug_center_8064'  # this contains the H2 plug sequences to bind to the new p8064 seed at the center of the x-slats
seed_plug_plate_all_8064 = 'P3643_MA_combined_seeds_8064'  # this contains the H2 plug sequences to bind to the new p8064 seed at both the edge and center of the x-slats

nelson_quimby_antihandles = 'sw_src005_antiNelsonQuimby_cc6hb_h2handles'  # this contains the full set of h2 handles for antiNelson/Quimby extensions
cnt_patterning = 'P3510_SSW_cnt_patterning'  # this contains h2, h5, and h1 extensions and DNA PAINT sequences for U Fribourg collab with CNT placement
octahedron_patterning_v1 = 'P3518_MA_octahedron_patterning_v1'  # this contains the H2 sequences for the octahedron patterning (diagonal) and H2/H5 strands for cross-bar binding
simpsons_mixplate_antihandles = 'sw_src007_nelson_quimby_bart_edna'  # this contains a variety of Bart, Edna, Nelson and Quimby handles for both H2 and H5
simpsons_mixplate_antihandles_maxed = 'sw_src010_nelson_quimby_bart_edna_maxed'  # this contains a variety of Bart, Edna, Nelson and Quimby handles for both H2 and H5 (500uM)
paint_h5_handles = 'P3628_SSW_plate' #this contains PAINT Probe 1 9nts dock strands for positions 1, 2, 4, 8, 16, 32, PAINT Probe 1 10nts dock strands for positions 1, 2, 4, 8, 16, 32,Biotinylated Quimby handle oligo for surface functionalization,D1-D4, E1-E4, F1-F4, G1-G4, H1-H4: first 4 6hb slat core staples for h1 -> h1, 5x orders of each for a total of 50 nmole each strand

def sanitize_plate_map(name):
    """
    Actual plate name for the Echo always just features the person's name and the plate ID.
    :param name: Long-form plate name
    :return: Barebones plate name for Echo
    """
    return name.split('_')[0] + '_' + name.split('_')[1]
