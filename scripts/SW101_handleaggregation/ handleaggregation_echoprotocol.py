import pandas as pd
import os
import numpy as np

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.assembly_handle_optimization.hamming_compute import multirule_precise_hamming
from crisscross.assembly_handle_optimization.random_hamming_optimizer import generate_handle_set_and_optimize
from crisscross.plate_mapping import get_standard_plates

DesignFolder = "/Users/stellawang/Dropbox (HMS)/crisscross_team/Crisscross Designs/SW101_handleaggregation"
#DesignFolder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/crisscross_code/scratch/design_testing_area/SW101_handleaggregation'

DesignFile = "layer_arrays.xlsx"
ReadHandlesFromFile = True

# Useful names and variables
LayerList = ["Layer_0", "Layer_1", "Layer_2"] 
OutputFilePrefix = "handle_array_layer_"

# Global variables are in PascalCase
# Local variables are in camelCase
# Functions and some repo constants are in snake_case

# reads in and formats slat design into a 3D array
DesignDF = pd.read_excel(os.path.join(DesignFolder, DesignFile), sheet_name=None, header=None)

# Prepare an empty dataframe and fill with slat positions
SlatArray = np.zeros((DesignDF[LayerList[0]].shape[0], DesignDF[LayerList[0]].shape[1], len(DesignDF)))
for i, key in enumerate(LayerList):
    SlatArray[..., i] = DesignDF[key].values

# Prepare to load handle assignments from file, but if not available, regenerate a fresh handle set
if ReadHandlesFromFile:  # this is to re-load a pre-computed handle array and save time later
    HandleArray = np.zeros((SlatArray.shape[0], SlatArray.shape[1], SlatArray.shape[2]-1))
    for i in range(SlatArray.shape[-1]-1):
        try:
            HandleArray[..., i] = np.loadtxt(os.path.join(DesignFolder, OutputFilePrefix + "%s.csv" % (i)), delimiter=',', encoding='utf-8-sig').astype(np.float32)
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

# Combines handle and slat array into the megastructure
HandleAggregateMegastructure = Megastructure(SlatArray, [2, (5, 2), (5,2), 5])
HandleAggregateMegastructure.assign_crisscross_handles(HandleArray, CrisscrossHandleXPlates, CrisscrossAntihandleYPlates)

# Patch up missing controls
HandleAggregateMegastructure.patch_control_handles(CorePlate)

# Exports design to echo format csv file for production
convert_slats_into_echo_commands(HandleAggregateMegastructure.slats, 'handleaggregation', DesignFolder, 'all_echo_commands.csv',
                                 default_transfer_volume=100)

# Filter out placeholder slats (anything above #25)
WantedSlats = ["-slat{}_".format(x) for x in list(np.arange(1,25+1,1))]
instructions = np.loadtxt(os.path.join(DesignFolder, 'all_echo_commands.csv'), delimiter=",",skiprows=1, dtype=str)

NewInstructions = []
for instruc in instructions:
    comment = instruc[0]
    for wantedSlat in WantedSlats:
        if wantedSlat in comment:
            NewInstructions.append(instruc)
            break
Header=['Component', 'Source Plate Name', 'Source Well', 'Destination Well', 'Transfer Volume',
        'Destination Plate Name', 'Source Plate Type']
np.savetxt(os.path.join(DesignFolder, 'all_echo_commands_filtered.csv'), [Header]+NewInstructions, delimiter=",", fmt="%s")
# Manually chance total volume per transfer for slats 1, 6, and 7 to 200
