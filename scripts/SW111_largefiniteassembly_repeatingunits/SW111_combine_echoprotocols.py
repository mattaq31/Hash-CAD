import pandas as pd
import os
import numpy as np

# Combine all echoprotocols into one

DesignFolder = "/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW111_large_repeating_units"
EchoFiles = ["alphabet_design_echo.csv", "end2xpure_design_echo.csv", "startdual_design_echo.csv", "startsingle_design_echo.csv"]

for EchoFile in EchoFiles:
    print("Loading file %s." % EchoFile)
    EchoProtocol = np.loadtxt(os.path.join(DesignFolder, EchoFile), delimiter=",", skiprows=1, dtype=str)
    try: 
        AllEchoProtocols = np.concatenate((AllEchoProtocols, EchoProtocol), axis=0)
    except NameError:
        AllEchoProtocols = EchoProtocol

AllEchoProtocolsDF = pd.DataFrame(AllEchoProtocols, columns=['Component', 'Source Plate Name', 'Source Well',
                                                        'Destination Well', 'Transfer Volume',
                                                        'Destination Plate Name', 'Source Plate Type'])

AllEchoProtocolsDF.to_csv(os.path.join(DesignFolder, "SW111_allechoprotocols.csv"), index=False)