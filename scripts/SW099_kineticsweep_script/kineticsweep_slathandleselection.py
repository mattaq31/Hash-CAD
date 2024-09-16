import pandas as pd
import os
import numpy as np

from crisscross.core_functions.megastructures import Megastructure
from crisscross.assembly_handle_optimization.hamming_compute import multirule_precise_hamming
from crisscross.assembly_handle_optimization.random_hamming_optimizer import generate_handle_set_and_optimize
from crisscross.plate_mapping import get_plateclass, get_standard_plates

from crisscross.helper_functions.plate_constants import cargo_plate_folder, nelson_quimby_antihandles

DesignFolder = "/Users/stellawang/Dropbox (HMS)/crisscross_team/Crisscross Designs/SW099_kineticsweep_design"
DesignFolder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/crisscross_code/scratch/design_testing_area/SW099_kineticsweep_design'

DesignFile = "SW099_kineticsweepfiniteribbon_design.xlsx"
ReadHandlesFromFile = False

# Useful names and variables
LayerList = ["Layer0_seed", "Layer1_X", "Layer2_Y", "Layer3_cargo"] # in order, seed at bottom and cargo on top
SeedLayer = "Layer0_seed"
CargoLayer = "Layer3_cargo"
OutputFilePrefix = "handle_array_layer"

# Global variables are in PascalCase
# Local variables are in camelCase
# Functions and some repo constants are in snake_case

# reads in and formats slat design into a 3D array
DesignDF = pd.read_excel(os.path.join(DesignFolder, DesignFile), sheet_name=None, header=None)

# Prepare an empty dataframe and fill with slat positions
SlatArray = np.zeros((DesignDF[LayerList[0]].shape[0], DesignDF[LayerList[0]].shape[1], len(DesignDF)-2))
for i, key in enumerate(LayerList[1:-1]):
    SlatArray[..., i] = DesignDF[key].values

# Prepare to load handle assignments from file, but if not available, regenerate a fresh handle set
if ReadHandlesFromFile:  # this is to re-load a pre-computed handle array and save time later
    HandleArray = np.zeros((SlatArray.shape[0], SlatArray.shape[1], SlatArray.shape[2]-1))
    for i in range(SlatArray.shape[-1]-1):
        try:
            HandleArray[..., i] = np.loadtxt(os.path.join(DesignFolder, OutputFilePrefix + "%s.csv" % (i+1)), delimiter=',').astype(np.float32)
        except FileNotFoundError:
            raise RuntimeError("No handle array file was found. Switch 'HandlesFromFile' flag to False and try again.")

    result = multirule_precise_hamming(SlatArray, HandleArray)
    print('Hamming distance from file-loaded design: %s' % result['Universal'])

else:
    HandleArray = generate_handle_set_and_optimize(SlatArray, unique_sequences=32, max_rounds=10)
    for i in range(HandleArray.shape[-1]):
        np.savetxt(os.path.join(DesignFolder, OutputFilePrefix + "%s.csv" % (i+1)),
                   HandleArray[..., i].astype(np.int32), delimiter=',', fmt='%i')

# Generates plate dictionaries from provided files - don't change
CorePlate, CrisscrossAntihandleYPlates, CrisscrossHandleXPlates, EdgeSeedPlate, CenterSeedPlate, CombinedSeedPlate = get_standard_plates()

CargoPlate = get_plateclass('GenericPlate', nelson_quimby_antihandles, cargo_plate_folder)
cargo_key = {3: 'antiNelson'}

# Combines handle and slat array into the megastructure
KineticMegastructure = Megastructure(SlatArray, [2, (5, 5), 2])
KineticMegastructure.assign_crisscross_handles(HandleArray, CrisscrossHandleXPlates, CrisscrossAntihandleYPlates)

# Prepare the seed layer and assign to array
SeedArray = DesignDF[SeedLayer].values
KineticMegastructure.assign_seed_handles(SeedArray, CenterSeedPlate, layer_id=1)

# Prepare the cargo layer, map cargo handle ids, and assign to array
CargoArray = DesignDF[CargoLayer].values
KineticMegastructure.assign_cargo_handles_with_array(CargoArray, cargo_key, CargoPlate, layer='top')

# Patch up missing controls
KineticMegastructure.patch_control_handles(CorePlate)
KineticMegastructure.create_standard_graphical_report(DesignFolder)
KineticMegastructure.create_blender_3D_view(DesignFolder, animate_assembly=True)

# Exports design to echo format csv file for production
# convert_slats_into_echo_commands(KineticMegastructure.slats, 'kineticsweep', DesignFolder, 'all_echo_commands.csv',
#                                  transfer_volume=100)

