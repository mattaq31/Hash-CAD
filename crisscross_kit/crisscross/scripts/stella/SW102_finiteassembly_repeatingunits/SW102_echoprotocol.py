import pandas as pd
import os
import numpy as np

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_precise_hamming
from crisscross.plate_mapping import get_standard_plates

#===== Main 4 units =====#

DesignFolder = "/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW102_SW103_repeatingunitsfiniteassembly_zigzagkinetics"
DesignFile = "actual_units_design.xlsx"

# Useful names and variables
LayerList = ["slat_layer_1", "slat_layer_2"] # "handle_layer_1"
SeedLayer = "seed_layer"
HandleArrayPrefix = "handle_layer_"

DesignDF = pd.read_excel(os.path.join(DesignFolder, DesignFile), sheet_name=None, header=None)

# Prepare an empty dataframe and fill with slat positions
SlatArray = np.zeros((DesignDF[LayerList[0]].shape[0], DesignDF[LayerList[0]].shape[1], len(LayerList)))
for i, key in enumerate(LayerList):
    SlatArray[..., i] = DesignDF[key].values

# Handles should have been prepared in the other script in this folder
HandleArray = np.zeros((SlatArray.shape[0], SlatArray.shape[1], SlatArray.shape[2]-1))
for i in range(SlatArray.shape[-1]-1):
    try:
        HandleArray[..., i] = DesignDF[HandleArrayPrefix+"%s" % (i+1)].values
        #HandleArray[..., i] = np.loadtxt(os.path.join(DesignFolder, HandleArrayPrefix + "%s.csv" % (i+1)), delimiter=',').astype(np.float32)
    except KeyError:
        raise RuntimeError("No handle array file was found. Use the other script to generate one.")

result = multirule_precise_hamming(SlatArray, HandleArray)
print('Hamming distance from file-loaded design: %s' % result['Universal']) ### Why did this report 26? Should be much lower
        
# Generates plate dictionaries from provided files - don't change
CorePlate, CrisscrossAntihandleYPlates, CrisscrossHandleXPlates, EdgeSeedPlate, CenterSeedPlate = get_standard_plates()

# Combines handle and slat array into the megastructure
FiniteAssemblyMegastructure = Megastructure(SlatArray, [2, (5, 2), 5])
FiniteAssemblyMegastructure.assign_assembly_handles(HandleArray, CrisscrossHandleXPlates, CrisscrossAntihandleYPlates)

# Prepare the seed layer and assign to array
SeedArray = DesignDF[SeedLayer].values
FiniteAssemblyMegastructure.assign_seed_handles(SeedArray, CenterSeedPlate, layer_id=1)

# Patch up missing controls
FiniteAssemblyMegastructure.patch_flat_staples(CorePlate)

# Specify wells for more intuitive echo protocol
EightByEightWells = [[x+str(y) for y in np.arange(1,8+1,1)] for x in ["A","B","C","D","E","F","G","H"]]
EightByEightWellsFlat = [item for sublist in EightByEightWells for item in sublist]

# Exports design to echo format csv file for production
convert_slats_into_echo_commands(FiniteAssemblyMegastructure.slats, 'finite_assembly_units', DesignFolder, 'finite_assembly_echo_commands.csv',
                                  transfer_volume=200, specific_plate_wells=EightByEightWellsFlat)

#===== Extra units: seed attachment right forward growth only, no seed attachment right growth unit =====#

DesignFileExtras = "actual_units_extras_design.xlsx"

# Variable/sheet names are same as above

DesignDFExtras = pd.read_excel(os.path.join(DesignFolder, DesignFileExtras), sheet_name=None, header=None)

# Prepare an empty dataframe and fill with slat positions
SlatArrayExtras = np.zeros((DesignDFExtras[LayerList[0]].shape[0], DesignDF[LayerList[0]].shape[1], len(LayerList)))
for i, key in enumerate(LayerList):
    SlatArrayExtras[..., i] = DesignDFExtras[key].values

# Handles should have been prepared in the other script in this folder
HandleArrayExtras = np.zeros((SlatArrayExtras.shape[0], SlatArrayExtras.shape[1], SlatArrayExtras.shape[2]-1))
for i in range(SlatArrayExtras.shape[-1]-1):
    try:
        HandleArrayExtras[..., i] = DesignDFExtras[HandleArrayPrefix+"%s" % (i+1)].values
        
    except KeyError:
        raise RuntimeError("No handle array file was found. Use the other script to generate one.")

resultExtra = multirule_precise_hamming(SlatArrayExtras, HandleArrayExtras)
print('Hamming distance from file-loaded design: %s' % resultExtra['Universal']) 

# Combines handle and slat array into the megastructure
FiniteAssemblyExtrasMegastructure = Megastructure(SlatArrayExtras, [2, (5, 2), 5])
FiniteAssemblyExtrasMegastructure.assign_assembly_handles(HandleArrayExtras, CrisscrossHandleXPlates, CrisscrossAntihandleYPlates)

# Prepare the seed layer and assign to array
SeedArrayExtras = DesignDFExtras[SeedLayer].values
FiniteAssemblyExtrasMegastructure.assign_seed_handles(SeedArrayExtras, CenterSeedPlate, layer_id=1)

# Patch up missing controls
FiniteAssemblyExtrasMegastructure.patch_flat_staples(CorePlate)

# Same Specific Wells as above

# Exports design to echo format csv file for production
convert_slats_into_echo_commands(FiniteAssemblyExtrasMegastructure.slats, 'finite_assembly_extras', DesignFolder, 'finite_assembly_extras_echo_commands.csv',
                                  transfer_volume=200, specific_plate_wells=EightByEightWellsFlat)
