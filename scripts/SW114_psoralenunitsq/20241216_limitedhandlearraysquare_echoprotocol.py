import numpy as np
import pandas as pd
import os

from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates

DesignFolder = "/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW114_psoralenunitsq"
DesignFile = "psoralensquare_H25.xlsx"
LayerListPrefix = "slat_layer_" 
HandleArrayPrefix = "handle_layer_"
CargoLayerPrefix = "cargo_layer_"
SeedLayer = "seed_layer"

########################################
# Make slat, handle (see associated jupyter notebook), and cargo position information in an excel sheet
# Load as np arrays here

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

########################################
# Map cargo handles, get plates
CorePlate, CrisscrossAntihandleYPlates, CrisscrossHandleXPlates, EdgeSeedPlate, CenterSeedPlate, CombinedSeedPlate = get_standard_plates()
src004, src005, src007, P3518, P3510 = get_cargo_plates()

cargo_key = {1:"antiSmithers-10mer", 2:"antiQuimby-10mer", 3:"antiPatty-10mer", 4:"antiMarge-10mer", 5:"antiLisa-10mer", 
             6:"antiKrusty-10mer", 7:"antiHomer-10mer", 8:"SSW041DoublePurification5primetoehold"}

########################################
# Generate Megastructure and save slats
PsoralenMegastructure = Megastructure(SlatArray, [2, (5, 2), 5])
PsoralenMegastructure.assign_crisscross_handles(HandleArray, CrisscrossHandleXPlates, CrisscrossAntihandleYPlates)

SeedArray = DesignDF[SeedLayer].values
PsoralenMegastructure.assign_seed_handles(SeedArray, CombinedSeedPlate, layer_id=1)

### Note on cargo: currently cannot mix multiple cargo plates. Will need to do double purification manually for now
# Skip top side cargo bc we don't have any
CargoArrayBottomCrossbeam = DesignDF[CargoLayerPrefix + "bottom_crossbeam"].values
PsoralenMegastructure.assign_cargo_handles_with_array(CargoArrayBottomCrossbeam, cargo_key, P3518, layer='bottom')

PsoralenMegastructure.patch_placeholder_handles([CrisscrossHandleXPlates, CrisscrossAntihandleYPlates, CombinedSeedPlate, P3518, src004], \
                                            ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed', 'Cargo', 'Cargo'])
PsoralenMegastructure.patch_control_handles(CorePlate)

BasicVolumeUnit = 75 # nL

########################################
# Specify wells for more intuitive echo protocol
EightByEightWellsCenter = [[(1,x+str(y)) for y in np.arange(3,10+1,1)] for x in ["A","B","C","D","E","F","G","H"]]
EightByEightWellsFlat = [item for sublist in EightByEightWellsCenter for item in sublist]
# Add crossbeams manually

convert_slats_into_echo_commands(PsoralenMegastructure.slats, "psoralen_unitsq", 
                                        DesignFolder, "SW114_psoralenunitsq_echoprotocol.csv",
                                        unique_transfer_volume_for_plates={'sw_src004': 200, "P3518_MA": 200,},
                                        default_transfer_volume=BasicVolumeUnit,
                                        manual_plate_well_assignments=EightByEightWellsFlat)
