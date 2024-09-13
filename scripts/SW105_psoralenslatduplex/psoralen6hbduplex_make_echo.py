import pandas as pd
import os
import numpy as np

from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.plate_mapping import get_plateclass, get_standard_plates

DesignFolder = "/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW105_6hbduplexpsoralen"
DesignFile = "handle_and_slat_arrays.xlsx"

# Useful names and variables
LayerList = ["handle_array_layer_1", "slat_layer_1", "slat_layer_2"]

DesignDF = pd.read_excel(os.path.join(DesignFolder, DesignFile), sheet_name=None, header=None)

# Prepare an empty dataframe and fill with slat positions
SlatArray = np.zeros((DesignDF[LayerList[0]].shape[0], DesignDF[LayerList[0]].shape[1], len(LayerList)-1))
for i, key in enumerate(LayerList[1:]):
    SlatArray[..., i] = DesignDF[key].values

# Load handles from file
HandleArray = np.zeros((SlatArray.shape[0], SlatArray.shape[1], SlatArray.shape[2]-1))
HandleArray[..., 0] = DesignDF[LayerList[0]].values

# Generates plate dictionaries from provided files - don't change
CorePlate, CrisscrossAntihandleYPlates, CrisscrossHandleXPlates, EdgeSeedPlate, CenterSeedPlate, CombinedSeedPlate = get_standard_plates()

# Combines handle and slat array into the megastructure
DuplexMegastructure = Megastructure(SlatArray)
DuplexMegastructure.assign_crisscross_handles(HandleArray, CrisscrossHandleXPlates, CrisscrossAntihandleYPlates)

# Patch up missing controls
DuplexMegastructure.patch_control_handles(CorePlate)
#DuplexMegastructure.create_standard_graphical_report(DesignFolder) # TODO: troubleshoot the pyvista errors

# Make Echo
specific_plate_wells = {"layer1-slat{}".format(x):(1, "B"+str(x)) for x in np.arange(1,3+1,1)}

for x in np.arange(4,6+1,1):
    specific_plate_wells["layer2-slat{}".format(x)] = (1, "B"+str(x))

convert_slats_into_echo_commands(slat_dict=DuplexMegastructure.slats,
                                destination_plate_name='psoralen_duplexes',
                                manual_plate_well_assignments=specific_plate_wells, default_transfer_volume=400,
                                output_folder=DesignFolder,
                                output_filename=f'echo_commands_psoralen_duplexes.csv')