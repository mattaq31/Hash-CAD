import pandas as pd
import os
import numpy as np
from copy import deepcopy

from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.assembly_handle_optimization.hamming_compute import multirule_precise_hamming
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates, get_plateclass
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.helper_functions.plate_constants import seed_plug_plate_center_8064, core_plate_folder

##### Design notes: just make 16 X slats (upper half) that uses the new seed in the center, combine with X2, Y1, and Y2 slat sets from MA018
##### Goal: check that the new library doesn't have spurious assembly, by solution assembly and by growth on bead (pulldown and supernatant)

DesignFolder = "/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW121_spuriousassembly"
LayerListPrefix = "slat_layer_" 
SeedLayer = "seed_layer"
HandleArrayPrefix = "handle_layer_"
DesignFile = "/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW121_spuriousassembly/newlibrary_spuriousassembly_design.xlsx"

RunAnalysis = False

# Input oligo plates

CorePlate, CrisscrossAntihandleYPlates, CrisscrossHandleXPlates, _, _, _ = (get_standard_plates(handle_library_v2=True)) # Use new assembly handle plates
P8064SeedPlate = get_plateclass('CombinedSeedPlugPlate', seed_plug_plate_center_8064, core_plate_folder) # And new P8064 seed plugs

# Specify wells for more intuitive echo protocol
EightByEightWells = [[(1,x+str(y)) for y in np.arange(3,10+1,1)] for x in ["A","B","C","D","E","F","G","H"]]
EightByEightWellsFlat = [item for sublist in EightByEightWells for item in sublist]

# Load in design
DesignDF = pd.read_excel(DesignFile, sheet_name=None, header=None)

# Prepare empty dataframe and populate with slats
SlatLayers = [x for x in DesignDF.keys() if LayerListPrefix in x]
SlatArray = np.zeros((DesignDF[SlatLayers[0]].shape[0], DesignDF[SlatLayers[0]].shape[1], len(SlatLayers)))
for i, key in enumerate(SlatLayers):
    SlatArray[..., i] = DesignDF[key].values

# Load in handles from the design sheet
HandleLayers = [x for x in DesignDF.keys() if HandleArrayPrefix in x]
HandleArray = np.zeros((DesignDF[HandleLayers[0]].shape[0], DesignDF[HandleLayers[0]].shape[1], len(HandleLayers)))
for i, key in enumerate(HandleLayers):
    HandleArray[..., i] = DesignDF[key].values

# Save the seed array
SeedArray = DesignDF[SeedLayer].values

# Handle the megastructure creation here
NewLibMega = Megastructure(SlatArray, [2, (5, 2), 5])
NewLibMega.assign_assembly_handles(HandleArray, CrisscrossHandleXPlates, CrisscrossAntihandleYPlates)
NewLibMega.assign_seed_handles(SeedArray, P8064SeedPlate, layer_id=1)

# No need for patching placeholders, would use this if the handle array is passed to Megastructure during initialization
#NewLibMega.patch_placeholder_handles(
#   [CrisscrossHandleXPlates, CrisscrossAntihandleYPlates, P8064SeedPlate], ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed'])

# Convert labels and handles into actual wells from source plates (patching)
NewLibMega.patch_flat_staples(CorePlate)

# Prepare Echo sheet, but only for the first 16 slats which are the nucX slats
NucXSlats = {}
for i in np.arange(1,16+1,1):
    slatname = "layer1-slat%s" % i
    NucXSlats[slatname] = NewLibMega.slats[slatname]

target_volume = 100 # Note that the concentrations for this library are much lower!

special_vol_plates = {'P3621_SSW': int(target_volume * (500 / 200)),
                        'P3518_MA': int(target_volume * (500 / 200)),
                        'P3601_MA': int(target_volume * (500 / 100)),
                        'P3602_MA': int(target_volume * (500 / 100)),
                        'P3603_MA': int(target_volume * (500 / 100)),
                        'P3604_MA': int(target_volume * (500 / 100)),
                        'P3605_MA': int(target_volume * (500 / 100)),
                        'P3606_MA': int(target_volume * (500 / 100))}

EchoSheet = convert_slats_into_echo_commands(slat_dict=NucXSlats,
                                             destination_plate_name="newlibrary_spurious_nucleation",
                                             unique_transfer_volume_for_plates=special_vol_plates,
                                             default_transfer_volume=target_volume,
                                             output_folder=DesignFolder,
                                             center_only_well_pattern=True,
                                             output_filename=f'newlibrary_x1_spurious_echo_commands.csv')

print("Finished making echo protocol for %s." % DesignFile)
