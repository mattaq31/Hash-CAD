import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt

from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.assembly_handle_optimization.hamming_compute import multirule_precise_hamming, multirule_oneshot_hamming
from crisscross.plate_mapping import get_standard_plates, get_cargo_plates

# GOAL: test that the multirule oneshot version works as intended, using the alphabet set for SW111

DesignFolder = "/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW111_large_repeating_units"
LayerListPrefix = "slat_layer_" 
SeedLayer = "seed_layer"
CargoLayer = "cargo_layer"
HandleArrayPrefix = "handle_layer_"

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
DesignFile = "alphabet_design_H29.xlsx"

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

# Test the oneshot versions
print("Testing oneshot version...")
result = multirule_oneshot_hamming(SlatArray, HandleArray, per_layer_check=True, specific_slat_groups=SlatGrouping, request_substitute_risk_score=True)

# First report Hamming distance measures if two sets of slat blocks are exposed to each other
print('Hamming distance (global): %s' % result['Universal']) 
print('Hamming distance (substitution risk): %s' % result['Substitute Risk'])
print('Hamming distance (groups Right & Up): %s' % result['Right-Up'])
print('Hamming distance (groups Left & Up): %s' % result['Left-Up'])
print('Hamming distance (groups Right & Down): %s' % result['Right-Down'])
print('Hamming distance (groups Left & Down): %s' % result['Left-Down'])

result_partial = multirule_oneshot_hamming(SlatArray, HandleArray, per_layer_check=True, request_substitute_risk_score=True, \
                                        partial_area_score=PartialAreaGrouping)

for subgroup in ["Right-Block1", "Right-Block2", "Left-Block1", "Left-Block2"]:
    print('Hamming distance ({} handle-antihandles): {}'.format(subgroup, result_partial[subgroup]))

if True: # Double check that the multirule precise version is also counting indices correctly
    print("Testing precise version...")
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