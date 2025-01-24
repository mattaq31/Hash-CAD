import pandas as pd
import os
import numpy as np

from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.assembly_handle_optimization.hamming_compute import multirule_precise_hamming
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates

DesignFolder = "/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW110_UFribourg_Design1-4xCNT_Design2"
LayerListPrefix = "slat_layer_" 
SeedLayer = "seed_layer"
CargoLayerPrefix = "cargo_layer_"
HandleArrayPrefix = "handle_layer_"

DesignFiles = ["design0_design_H29.xlsx", "design1_design_H29.xlsx", "design2_design_H29.xlsx"]
PlateNames = ["Design0-Control", "Design1-4xCNT", "Design2-trench"]
OutfileNames = ["design0-control_echo.csv", "design1-4xCNT_echo.csv", "design2-trench_echo.csv"]

ReMakeEchoProtocols = True

# Notes: nothing other than CNT binding sequences this time - handle extensions, probe handles, or DNA PAINT sites

# Generic initializations
CorePlate, CrisscrossAntihandleYPlates, CrisscrossHandleXPlates, EdgeSeedPlate, CenterSeedPlate, CombinedSeedPlate = get_standard_plates()
src004, src005, src007, P3518, P3510 = get_cargo_plates()
design1cnt_key = {2 : "CNTbindingL2prime",
                  3: "CNTbindingL2",
                  1 : "SSW041DoublePurification5primetoehold"}
# Note that this must be the cargo "name" (the first string before the first underscore) and not including the h2/h5 or position

# Specify wells for more intuitive echo protocol
EightByEightWellsCenter = [[(1,x+str(y)) for y in np.arange(3,10+1,1)] for x in ["A","B","C","D","E","F","G","H"]]
EightByEightWellsFlat = [item for sublist in EightByEightWellsCenter for item in sublist]

# Design 0 - Control without CNT handles and Design 1 - 2 x 4-CNT. Typical crisscross design, so use the repo code

if ReMakeEchoProtocols:
    for nFile, DesignFile in enumerate(DesignFiles):
        # Load info and initialize dataframe by loading info/design sheets
        DesignDF = pd.read_excel(os.path.join(DesignFolder, DesignFile), sheet_name=None, header=None)

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

        DesignMegastructure = Megastructure(SlatArray, [2, (5, 2), 5])
        DesignMegastructure.assign_crisscross_handles(HandleArray, CrisscrossHandleXPlates, CrisscrossAntihandleYPlates)

        SeedArray = DesignDF[SeedLayer].values
        DesignMegastructure.assign_seed_handles(SeedArray, CombinedSeedPlate, layer_id=1)

        if nFile == 1: # only applies to Design 1
            CargoArrayTop = DesignDF[CargoLayerPrefix + "top"].values
            DesignMegastructure.assign_cargo_handles_with_array(CargoArrayTop, design1cnt_key, P3510, layer='top')

        CargoArrayBottom = DesignDF[CargoLayerPrefix + "bottom"].values
        DesignMegastructure.assign_cargo_handles_with_array(CargoArrayBottom, design1cnt_key, src004, layer='bottom')

        # Convert labels and handles into actual wells from source plates (patching)
        DesignMegastructure.patch_placeholder_handles([CrisscrossHandleXPlates, CrisscrossAntihandleYPlates, CombinedSeedPlate, P3510, src004], \
                                                    ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo'])
        DesignMegastructure.patch_control_handles(CorePlate)

        BasicVolumeUnit = 75 # nL

        convert_slats_into_echo_commands(DesignMegastructure.slats, PlateNames[nFile], 
                                        DesignFolder, OutfileNames[nFile],
                                        unique_transfer_volume_for_plates={'sw_src004': 200, "P3510_SSW": 200,},
                                        default_transfer_volume=BasicVolumeUnit,
                                        manual_plate_well_assignments=EightByEightWellsFlat)
        
        # Volume for non-standard plates should be 187, but Echo transfers in units of 25
        print("Finished making echo protocol for Design %s." % nFile)

# Design 2 - Previously was just Design 0, but add a corner preparing h1-swapped core staples - do this in a jupyter notebook
