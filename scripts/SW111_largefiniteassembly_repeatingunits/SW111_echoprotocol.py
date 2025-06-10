import pandas as pd
import os
import numpy as np

from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.assembly_handle_optimization.hamming_compute import multirule_precise_hamming
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates

# Repurpose H29 for repeating unit assembly, maximizing the Hamming distance of the exposed 16x16 growing region against the 32x16 new set of slats
# Note: when creating slat/handle arrays with xlsx, pad everything with 0 that doesn't have a slat or handle, but is otherwise occupied in another layer

DesignFolder = "/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW111_large_repeating_units"
LayerListPrefix = "slat_layer_" 
SeedLayer = "seed_layer"
CargoLayer = "cargo_layer"
HandleArrayPrefix = "handle_layer_"

RunAnalysis = True

# Generic initializations
CorePlate, CrisscrossAntihandleYPlates, CrisscrossHandleXPlates, EdgeSeedPlate, CenterSeedPlate, CombinedSeedPlate = get_standard_plates()
src004, src005, src007, P3518 = get_cargo_plates()
doublepure_key = {1 : "SSW041DoublePurification5primetoehold"}

# Specify wells for more intuitive echo protocol
EightByEightWells = [[(1,x+str(y)) for y in np.arange(1,8+1,1)] for x in ["A","B","C","D","E","F","G","H"]]
EightByEightWellsFlat = [item for sublist in EightByEightWells for item in sublist]

# Slat grouping for the whole slat (all 32 handles) and partial slat (16 handles exposed during growth) Hamming distance calculations
SlatGrouping = {"Right-Up":[(1, x) for x in np.arange(1,16+1,1)] + [(2,y) for y in np.arange(33,48+1,1)], \
                "Left-Up":[(1, x) for x in np.arange(17,32+1,1)] + [(2,y) for y in np.arange(33,48+1,1)], \
                "Right-Down":[(1, x) for x in np.arange(1,16+1,1)] + [(2,y) for y in np.arange(49,64+1,1)], \
                "Left-Down":[(1, x) for x in np.arange(17,32+1,1)] + [(2,y) for y in np.arange(49,64+1,1)], }

# Calculate the restricted growth region Hamming distance against new slats from the next growth block
PartialAreaGrouping = {"Right-Block1":{}, "Right-Block2":{}, "Left-Block1":{}, "Left-Block2":{}}

# Right growth slats against antihandle set for Block 1
PartialAreaGrouping["Right-Block1"]["handles"] = {}
for slatID in np.arange(1,16+1,1):
    PartialAreaGrouping["Right-Block1"]["handles"][(1,slatID)] = [True for _ in np.arange(0,32,1)]

PartialAreaGrouping["Right-Block1"]["antihandles"] = {}
for slatID in np.arange(49,64+1,1):
    PartialAreaGrouping["Right-Block1"]["antihandles"][(2,slatID)] = [True for _ in np.arange(0,16,1)] + [False for _ in np.arange(0,16,1)]

# Right growth slats against antihandle set for Block 2
PartialAreaGrouping["Right-Block2"]["handles"] = {}
for slatID in np.arange(1,16+1,1):
    PartialAreaGrouping["Right-Block2"]["handles"][(1,slatID)] = [True for _ in np.arange(0,32,1)]

PartialAreaGrouping["Right-Block2"]["antihandles"] = {}
for slatID in np.arange(33,48+1,1):
    PartialAreaGrouping["Right-Block2"]["antihandles"][(2,slatID)] = [True for _ in np.arange(0,16,1)] + [False for _ in np.arange(0,16,1)]

# Left growth slats against handle set for Block 1
PartialAreaGrouping["Left-Block1"]["handles"] = {}
for slatID in np.arange(17,32+1,1):
    PartialAreaGrouping["Left-Block1"]["handles"][(1,slatID)] = [True for _ in np.arange(0,32,1)]

PartialAreaGrouping["Left-Block1"]["antihandles"] = {}
for slatID in np.arange(49,64+1,1):
    PartialAreaGrouping["Left-Block1"]["antihandles"][(2,slatID)] = [True for _ in np.arange(0,16,1)] + [False for _ in np.arange(0,16,1)]

# Left growth slats against handle set for Block 2
PartialAreaGrouping["Left-Block2"]["handles"] = {}
for slatID in np.arange(17,32+1,1):
    PartialAreaGrouping["Left-Block2"]["handles"][(1,slatID)] = [True for _ in np.arange(0,32,1)]

PartialAreaGrouping["Left-Block2"]["antihandles"] = {}
for slatID in np.arange(33,48+1,1):
    PartialAreaGrouping["Left-Block2"]["antihandles"][(2,slatID)] = [True for _ in np.arange(0,16,1)] + [False for _ in np.arange(0,16,1)]

# List of files to processs
DesignFiles = ["alphabet_design_H29.xlsx", "end2xpure_design_H29.xlsx", "startdual_design_H29.xlsx", "startsingle_design_H29.xlsx"]

FileSpecificInfoDict = {}
FileSpecificInfoDict["alphabet_design_H29.xlsx"] = {"interfaces": [2, (5, 2), 5], 
                                                    "Transfer Volume": 300, 
                                                    "Seed": False,
                                                    "Export Slat Layers":[1,2],
                                                    "Specific Wells": EightByEightWellsFlat, 
                                                    "Destination Plate":"alphabet_design"}
FileSpecificInfoDict["end2xpure_design_H29.xlsx"] = {"interfaces": [2, (5, 2), 5],
                                                     "Transfer Volume": 100, 
                                                     "Seed": False,
                                                     "Export Slat Layers":[1],
                                                     "Specific Wells": EightByEightWellsFlat[:16],
                                                     "Destination Plate":"start_and_end"}
FileSpecificInfoDict["startdual_design_H29.xlsx"] = {"interfaces": [2, (5, 2), 5], 
                                                     "Transfer Volume": 100, 
                                                     "Seed": True, 
                                                     "Export Slat Layers":[1],
                                                     "Specific Wells": EightByEightWellsFlat[16:32],
                                                     "Destination Plate":"start_and_end"}
FileSpecificInfoDict["startsingle_design_H29.xlsx"] = {"interfaces": [2, (5, 2), 5], 
                                                       "Transfer Volume": 100, 
                                                       "Seed": True, 
                                                       "Export Slat Layers":[1],
                                                       "Specific Wells": EightByEightWellsFlat[32:48],
                                                       "Destination Plate":"start_and_end"}

# Slat IDs:
# 1-16: Right
# 17-32: Left
# 33-48: Up
# 49-64: Down
# 65-80: End (2x purification); fill rest with 0 to have matched slats in all layers
# 81-96: Start dual; fill rest with 0 to have matched slats in all layers
# 97-112: Start single; fill rest with 0 to have matched slats in all layers

for i, DesignFile in enumerate(DesignFiles):
    print("Working on file {}".format(DesignFile))

    # Initialize dataframe by loading info/design sheets
    DesignDF = pd.read_excel(os.path.join(DesignFolder, "final", DesignFile), sheet_name=None, header=None)

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
    if "alphabet_design_H29.xlsx" in DesignFile and RunAnalysis:
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
    
        for subgroup in ["Right-Block1", "Right-Block2", "Left-Block1", "Left-Block2"]:
            print('Hamming distance ({} handle-antihandles): {}'.format(subgroup, result_partial[subgroup]))

    # Handle the megastructure creation here
    MyMegastructure = Megastructure(SlatArray, FileSpecificInfoDict[DesignFile]["interfaces"])
    MyMegastructure.assign_assembly_handles(HandleArray, CrisscrossHandleXPlates, CrisscrossAntihandleYPlates)

    if FileSpecificInfoDict[DesignFile]["Seed"]:
        SeedArray = DesignDF[SeedLayer].values
        MyMegastructure.assign_seed_handles(SeedArray, CombinedSeedPlate, layer_id=1)
    
    if CargoLayer in DesignDF.keys():
        CargoArray = DesignDF[CargoLayer].values
        MyMegastructure.assign_cargo_handles_with_array(CargoArray, doublepure_key, layer='bottom')
    
    # Convert labels and handles into actual wells from source plates (patching)
    MyMegastructure.patch_placeholder_handles([CrisscrossHandleXPlates, CrisscrossAntihandleYPlates, CombinedSeedPlate, src004], \
                                              ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo'])
    MyMegastructure.patch_flat_staples(CorePlate)

    # Generate csv file for each set of sequences, combine them later (add volume to the echo command generating funtion)
    # Filter out only the slats we need
    FilteredSlats = {key: slat for key, slat in MyMegastructure.slats.items() if slat.layer in FileSpecificInfoDict[DesignFile]["Export Slat Layers"]}
    convert_slats_into_echo_commands(FilteredSlats, FileSpecificInfoDict[DesignFile]["Destination Plate"], DesignFolder, DesignFile[:-9] + "_echo.csv",
                                     unique_transfer_volume_for_plates={'sw_src004': int(100*(500/200))},
                                     default_transfer_volume=FileSpecificInfoDict[DesignFile]["Transfer Volume"],
                                     manual_plate_well_assignments=FileSpecificInfoDict[DesignFile]["Specific Wells"])
    
    print("Finished making echo protocol for %s." % DesignFile)
