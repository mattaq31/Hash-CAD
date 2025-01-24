import pandas as pd
import os
import numpy as np

# Combine all echoprotocols into one

DesignFolder = "/Users/stellawang/HMS Dropbox/Siyuan Wang/crisscross_team/Crisscross Designs/SW110_UFribourg_Design1-4xCNT_Design2"
EchoFiles = ["design0-control_echo.csv", "design1-4xCNT_echo.csv", "design2-trench_echo.csv", "design2-trench_echo_extras.csv"]

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

AllEchoProtocolsDF.to_csv(os.path.join(DesignFolder, "SW110_allechoprotocols.csv"), index=False)