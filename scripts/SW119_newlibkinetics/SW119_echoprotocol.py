import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt

from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.assembly_handle_optimization.hamming_compute import multirule_precise_hamming
from crisscross.plate_mapping import get_standard_plates
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets

DesignFolder = "/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW119_newlibkinetics"
LayerListPrefix = "slat_layer_" 
SeedLayer = "seed_layer"
HandleArrayPrefix = "handle_layer_"
DesignFile = "/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW119_newlibkinetics/newlibrary_zigzagribbon_design.xlsx"

RunAnalysis = False

CorePlate, CrisscrossAntihandleYPlates, CrisscrossHandleXPlates, EdgeSeedPlate, CenterSeedPlate, CombinedSeedPlate = get_standard_plates()

# Specify wells for more intuitive echo protocol
EightByEightWells = [[(1,x+str(y)) for y in np.arange(3,10+1,1)] for x in ["A","B","C","D","E","F","G","H"]]
EightByEightWellsFlat = [item for sublist in EightByEightWells for item in sublist]

# In terms of Hamming calculation, we are testing possible interactions between slats (self-substition) and whether the next growth attaches correctly to the exposed region

SlatGrouping = {"Right-Up":[(1, x) for x in np.arange(1,16+1,1)] + [(2,y) for y in np.arange(17,32+1,1)]}

PartialAreaGrouping = {"Right1-Up1":{}, "Right1-Up2":{}}

# Right growth slats against antihandle set for Block 1
PartialAreaGrouping["Right1-Up1"]["handles"] = {}
for slatID in np.arange(1,16+1,1):
    #PartialAreaGrouping["Right1-Up1"]["handles"][(1,slatID)] = [False for _ in np.arange(0,16,1)] + [True for _ in np.arange(0,16,1)]
    PartialAreaGrouping["Right1-Up1"]["handles"][(1,slatID)] = [True for _ in np.arange(0,32,1)]

PartialAreaGrouping["Right1-Up1"]["antihandles"] = {}
for slatID in np.arange(17,32+1,1):
    PartialAreaGrouping["Right1-Up1"]["antihandles"][(2,slatID)] = [False for _ in np.arange(0,16,1)] + [True for _ in np.arange(0,16,1)]

# Right growth slats against antihandle set for Block 2
PartialAreaGrouping["Right1-Up2"]["handles"] = {}
for slatID in np.arange(1,16+1,1):
    #PartialAreaGrouping["Right1-Up2"]["handles"][(1,slatID)] = [False for _ in np.arange(0,16,1)] + [True for _ in np.arange(0,16,1)]
    PartialAreaGrouping["Right1-Up2"]["handles"][(1,slatID)] = [True for _ in np.arange(0,32,1)]

PartialAreaGrouping["Right1-Up2"]["antihandles"] = {}
for slatID in np.arange(17,32+1,1):
    PartialAreaGrouping["Right1-Up2"]["antihandles"][(2,slatID)] = [True for _ in np.arange(0,16,1)] + [False for _ in np.arange(0,16,1)]

# Slat IDs:
# 1-16: Right (has center old P8634 seed)
# 17-32: Up

# Block 1 has 3 in the top left corner, 1 in the bottom right
# Block 2 has 25 on both top left and bottom right corners, 27 on bottom left and 24 on top right
# The design has
# 0 2
# 2 1

# Import the design info

# Initialize dataframe by loading info/design sheets
DesignDF = pd.read_excel(DesignFile, sheet_name=None, header=None)

# Prepare empty dataframe and populate with slats
SlatLayers = [x for x in DesignDF.keys() if LayerListPrefix in x]
SlatArray = np.zeros((DesignDF[SlatLayers[0]].shape[0], DesignDF[SlatLayers[0]].shape[1], len(SlatLayers)))
for i, key in enumerate(SlatLayers):
    SlatArray[..., i] = DesignDF[key].values

# Load in handles from the previously loaded design sheet; separate sheet counting from slats to accommodate "unmatched" X-Y slats
HandleLayers = [x for x in DesignDF.keys() if HandleArrayPrefix in x]
HandleArray = np.zeros((DesignDF[HandleLayers[0]].shape[0], DesignDF[HandleLayers[0]].shape[1], len(HandleLayers)))
for i, key in enumerate(HandleLayers):
    HandleArray[..., i] = DesignDF[key].values

# Save the seed array
SeedArray = DesignDF[SeedLayer].values

# Don't do Hamming distance calculation for the "add-ons", just the square "alphabet" design
if RunAnalysis:
    result = multirule_precise_hamming(SlatArray, HandleArray, per_layer_check=True, specific_slat_groups=SlatGrouping, request_substitute_risk_score=True)

    # First report Hamming distance measures if two sets of slat blocks are exposed to each other
    print('Hamming distance (global): %s' % result['Universal']) 
    print('Hamming distance (substitution risk): %s' % result['Substitute Risk'])
    print('Hamming distance (groups Right): %s' % result['Right-Up'])
    
    result_partial = multirule_precise_hamming(SlatArray, HandleArray, per_layer_check=True, request_substitute_risk_score=True, \
                                            partial_area_score=PartialAreaGrouping)

    for subgroup in ["Right1-Up1", "Right1-Up2"]:
        print('Hamming distance ({} handle-antihandles): {}'.format(subgroup, result_partial[subgroup]))

# Handle the megastructure creation here
OldLibraryMega = Megastructure(SlatArray, [2, (5, 2), 5])
OldLibraryMega.assign_crisscross_handles(HandleArray, CrisscrossHandleXPlates, CrisscrossAntihandleYPlates)
OldLibraryMega.assign_seed_handles(SeedArray, CombinedSeedPlate, layer_id=1)

# Convert labels and handles into actual wells from source plates (patching)
#OldLibraryMega.patch_placeholder_handles([CrisscrossHandleXPlates, CrisscrossAntihandleYPlates, CombinedSeedPlate], \
#                                            ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed'])
OldLibraryMega.patch_control_handles(CorePlate)

# Generate csv file for each set of sequences, combine them later (add volume to the echo command generating funtion)
# Filter out only the slats we need

convert_slats_into_echo_commands(OldLibraryMega.slats, "old_vs_new_library_kinetics", 
                                 DesignFolder, "SW119_zigzag_oldlibrary_echo.csv",
                                 default_transfer_volume=200,
                                 manual_plate_well_assignments=EightByEightWellsFlat[:32])

print("Finished making echo protocol for %s." % DesignFile)


# Make the exact same slats but for the new library: Note, may need to watch for wells with higher or lower volumes/concentrations 
# - should be accounted for in the code

# Get new assembly handle plates
_, v2_crisscross_antihandle_y_plates, v2_crisscross_handle_x_plates, _, _, _ = get_standard_plates(handle_library_v2=True)

NewLibraryMega = Megastructure(SlatArray, [2, (5, 2), 5])
NewLibraryMega.assign_crisscross_handles(HandleArray, v2_crisscross_handle_x_plates, v2_crisscross_antihandle_y_plates)
NewLibraryMega.assign_seed_handles(SeedArray, CombinedSeedPlate, layer_id=1)
NewLibraryMega.patch_control_handles(CorePlate)

NewLibraryVolume = 100 # nl

# New library is at 100 µM, not 500 µM
special_vol_plates = {'P3601_MA': int(NewLibraryVolume * (500 / 100)),
                      'P3602_MA': int(NewLibraryVolume * (500 / 100)),
                      'P3603_MA': int(NewLibraryVolume * (500 / 100)),
                      'P3604_MA': int(NewLibraryVolume * (500 / 100)),
                      'P3605_MA': int(NewLibraryVolume * (500 / 100)),
                      'P3606_MA': int(NewLibraryVolume * (500 / 100))}

# Note: this makes the total expected volume per well to be 200 nL * 32 + 1 µL * 32 = 38.4 µL, which is much higher than should be used as
# a destination on the 96-well PCR plate
# So let's split this in half across two plates - use 100 nL transfer volume instead of 200 nL and manually copy instructions to a second plate

EchoSheetNew = convert_slats_into_echo_commands(NewLibraryMega.slats, "old_vs_new_library_kinetics", 
                                 DesignFolder, "SW119_zigzag_newlibrary_echo.csv",
                                 default_transfer_volume=NewLibraryVolume,
                                 unique_transfer_volume_for_plates=special_vol_plates,
                                 manual_plate_well_assignments=EightByEightWellsFlat[-32:])

prepare_all_standard_sheets(NewLibraryMega.slats, os.path.join(DesignFolder, 'newlibrary_standard_helpers.xlsx'),
                            reference_single_handle_volume=NewLibraryVolume,
                            reference_single_handle_concentration=500,
                            slat_mixture_volume="max",
                            echo_sheet=EchoSheetNew,
                            peg_groups_per_layer=1)



