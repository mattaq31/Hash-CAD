import pandas as pd
import os
import numpy as np

FilePathPrefix = "/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW102_repeating_SW103_zigzag_Magnonics_combined"

# Task: combine all echo protocols into one big protocol csv file
# Note the magnonics files need different names

MagnonicsFiles = ["echo_commands_dbl_crossbar_best_array.csv", "echo_commands_dbl_crossbar_random_handle_array.csv" ,\
                  "echo_commands_dbl_crossbar_reduced_handle_array.csv"]
MagnonicsPlateNames = ["best_Ham29", "random16_Ham24", "reduced16_Ham27"]

RepeatingUnitsFiles = ["finite_assembly_echo_commands.csv", "finite_assembly_extras_echo_commands.csv"]

CombinedProtocol = []

CombinedProtocolFilename = "all_echo_commands_combined.csv"

for i, filename in enumerate(MagnonicsFiles):
    FilePath = os.path.join(FilePathPrefix, filename)
    EchoProtocol = np.loadtxt(FilePath, skiprows=1, delimiter=',', dtype=str)
    for instruction in EchoProtocol:
        newLine = list(instruction[:5]) + [MagnonicsPlateNames[i]] + list(instruction[-1:])
        CombinedProtocol += [newLine]

for filename in RepeatingUnitsFiles:
    FilePath = os.path.join(FilePathPrefix, filename)
    EchoProtocol = np.loadtxt(FilePath, skiprows=1, delimiter=',', dtype=str)
    CombinedProtocol += [list(x) for x in EchoProtocol]
    
columns = ['Component', 'Source Plate Name', 'Source Well', 'Destination Well', 'Transfer Volume', 'Destination Plate Name', 'Source Plate Type']

np.savetxt(os.path.join(FilePathPrefix,CombinedProtocolFilename), [columns]+CombinedProtocol, delimiter=",", fmt="%s")