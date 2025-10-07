import pandas as pd
import os
import numpy as np

from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_precise_hamming
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates

# Very simple design, really just two slats with a specific handle set

# Conditions: 
# 5' TT (linkers) on both
# 5' TT on handles + 5' and 3' TT's on anti-handles
# 5' and 3' TT on handles + 5' TT on anti-handles
# 5' and 3' TT both

# Use the Crisscross repo code to make the 5' TT only version, then use Jupyter to process the 5' and 3' TT version

DesignFolder = "/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW113_psoralen3primeTT"
LayerListPrefix = "slat_layer_" 
HandleArrayPrefix = "handle_layer_"

DesignFile = "psoralenduplex_design.xlsx"
PlateName = "psoralen_duplex"
OutfileName = "psoralen-duplex_echo.csv"

CorePlate, CrisscrossAntihandleYPlates, CrisscrossHandleXPlates, EdgeSeedPlate, CenterSeedPlate, CombinedSeedPlate = get_standard_plates()

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

DuplexMegastructure = Megastructure(SlatArray, [2, (5, 2), 5])
DuplexMegastructure.assign_assembly_handles(HandleArray, CrisscrossHandleXPlates, CrisscrossAntihandleYPlates)

DuplexMegastructure.patch_placeholder_handles([CrisscrossHandleXPlates, CrisscrossAntihandleYPlates], \
                                                    ['Assembly-Handles', 'Assembly-AntiHandles'])

DuplexMegastructure.patch_flat_staples(CorePlate)

BasicVolumeUnit = 100 # nL

convert_slats_into_echo_commands(DuplexMegastructure.slats, PlateName, 
                                DesignFolder, OutfileName,
                                default_transfer_volume=BasicVolumeUnit)
