import pandas as pd
import os
import numpy as np

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.hamming_functions import generate_handle_set_and_optimize, multi_rule_hamming
from crisscross.plate_mapping import get_plateclass, get_standard_plates

DesignFolder = "/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW102_SW103_repeatingunitsfiniteassembly_zigzagkinetics"

DesignFile = "handleselection_arrays.xlsx"
ReadHandlesFromFile = True

# Useful names and variables
LayerList = ["selecthandles_slat_layer_1", "selecthandles_slat_layer_2"]
SeedLayer = "seed_layer"
OutputFilePrefix = "handle_array_layer_"

DesignDF = pd.read_excel(os.path.join(DesignFolder, DesignFile), sheet_name=None, header=None)

# Prepare an empty dataframe and fill with slat positions
SlatArray = np.zeros((DesignDF[LayerList[0]].shape[0], DesignDF[LayerList[0]].shape[1], len(LayerList)))
for i, key in enumerate(LayerList):
    SlatArray[..., i] = DesignDF[key].values

# Prepare to load handle assignments from file, but if not available, regenerate a fresh handle set
if ReadHandlesFromFile:  # this is to re-load a pre-computed handle array and save time later
    HandleArray = np.zeros((SlatArray.shape[0], SlatArray.shape[1], SlatArray.shape[2]-1))
    for i in range(SlatArray.shape[-1]-1):
        try:
            HandleArray[..., i] = np.loadtxt(os.path.join(DesignFolder, OutputFilePrefix + "%s.csv" % (i+1)), delimiter=',').astype(np.float32)
        except FileNotFoundError:
            raise RuntimeError("No handle array file was found. Switch 'HandlesFromFile' flag to False and try again.")

    result = multi_rule_hamming(SlatArray, HandleArray)
    print('Hamming distance from file-loaded design: %s' % result['Universal'])

else:
    HandleArray = generate_handle_set_and_optimize(SlatArray, unique_sequences=32, max_rounds=500)
    for i in range(HandleArray.shape[-1]):
        np.savetxt(os.path.join(DesignFolder, OutputFilePrefix + "%s.csv" % (i+1)),                   HandleArray[..., i].astype(np.int32), delimiter=',', fmt='%i')

# Hamming dist at 28

# Generates plate dictionaries from provided files - don't change
CorePlate, CrisscrossAntihandleYPlates, CrisscrossHandleXPlates, EdgeSeedPlate, CenterSeedPlate = get_standard_plates()

# Combines handle and slat array into the megastructure
TestMegastructure = Megastructure(SlatArray, [2, (5, 5), 2])
TestMegastructure.assign_crisscross_handles(HandleArray, CrisscrossHandleXPlates, CrisscrossAntihandleYPlates)

# Prepare the seed layer and assign to array
SeedArray = DesignDF[SeedLayer].values
TestMegastructure.assign_seed_handles(SeedArray, CenterSeedPlate, layer_id=1)

# Patch up missing controls
TestMegastructure.patch_control_handles(CorePlate)
TestMegastructure.create_standard_graphical_report(DesignFolder)
TestMegastructure.create_blender_3D_view(DesignFolder, animate_assembly=True)