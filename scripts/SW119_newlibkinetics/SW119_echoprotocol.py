import pandas as pd
import os
import numpy as np

from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.assembly_handle_optimization.hamming_compute import multirule_precise_hamming
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates

DesignFolder = "/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW119_newlibkinetics"
LayerListPrefix = "slat_layer_" 
SeedLayer = "seed_layer"
HandleArrayPrefix = "handle_layer_"
DesignFile = "/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW119_newlibkinetics/newlibrary_zigzagribbon_design.xlsx"

RunAnalysis = True

CorePlate, CrisscrossAntihandleYPlates, CrisscrossHandleXPlates, EdgeSeedPlate, CenterSeedPlate, CombinedSeedPlate = get_standard_plates()

# Specify wells for more intuitive echo protocol
EightByEightWells = [[(1,x+str(y)) for y in np.arange(1,8+1,1)] for x in ["A","B","C","D","E","F","G","H"]]
EightByEightWellsFlat = [item for sublist in EightByEightWells for item in sublist]

# In terms of Hamming calculation, we are testing possible interactions between slats (self-substition) and whether the next growth attaches correctly to the exposed region

SlatGrouping = {"Right":[(1, x) for x in np.arange(1,16+1,1)], "Up":[(2, x) for x in np.arange(17,32+1,1)]}

PartialAreaGrouping = {"Right1-Up1":{}, "Right1-Up2":{}}

# Right growth slats against antihandle set for Block 1
PartialAreaGrouping["Right1-Up1"]["handles"] = {}
for slatID in np.arange(1,16+1,1):
    PartialAreaGrouping["Right1-Up1"]["handles"][(1,slatID)] = [False for _ in np.arange(0,16,1)] + [True for _ in np.arange(0,16,1)]

PartialAreaGrouping["Right1-Up1"]["antihandles"] = {}
for slatID in np.arange(17,32+1,1):
    PartialAreaGrouping["Right1-Up1"]["antihandles"][(2,slatID)] = [False for _ in np.arange(0,16,1)] + [True for _ in np.arange(0,16,1)]

# Right growth slats against antihandle set for Block 2
PartialAreaGrouping["Right1-Up2"]["handles"] = {}
for slatID in np.arange(1,16+1,1):
    PartialAreaGrouping["Right1-Up2"]["handles"][(1,slatID)] = [False for _ in np.arange(0,16,1)] + [True for _ in np.arange(0,16,1)]

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

# Don't do Hamming distance calculation for the "add-ons", just the square "alphabet" design
if RunAnalysis:
    result = multirule_precise_hamming(SlatArray, HandleArray, per_layer_check=True, specific_slat_groups=SlatGrouping, request_substitute_risk_score=True)

    # First report Hamming distance measures if two sets of slat blocks are exposed to each other
    print('Hamming distance (global): %s' % result['Universal']) 
    print('Hamming distance (substitution risk): %s' % result['Substitute Risk'])
    print('Hamming distance (groups Right & Up): %s' % result['Right-Up'])
    print('Hamming distance (groups Left & Up): %s' % result['Left-Up'])
    print('Hamming distance (groups Right & Down): %s' % result['Right-Down'])
    print('Hamming distance (groups Left & Down): %s' % result['Left-Down'])
    
    result_partial = multirule_precise_hamming(SlatArray, HandleArray, per_layer_check=True, request_substitute_risk_score=True, \
                                            partial_area_score=PartialAreaGrouping)

    for subgroup in ["Right1-Up1", "Right1-Up2"]:
        print('Hamming distance ({} handle-antihandles): {}'.format(subgroup, result_partial[subgroup]))

# Make the exact same slats but for the new library: Note, may need to watch for wells with higher or lower volumes/concentrations 
# - should be accounted for in the code



