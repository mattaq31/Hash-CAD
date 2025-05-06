from sequence_picking_tools import *
import pickle
import matplotlib.pyplot as plt
import numpy as np
import time
from collections import Counter



if __name__ == '__main__':
    # Start caffeinate in the background
    #caffeinate = subprocess.Popen(['caffeinate', '-i'])


    # open the preselected prossible handle sequences as dictionary
    name= 'TT_no_crosscheck96to108'

    with open(name + '.pkl',  'rb') as f:
        handle_energy_dict = pickle.load(f)

    handles = list(handle_energy_dict.keys())
    print(len(handles))

    crossdick = selfvalidate(handles, Use_Library=True)

    # Save the new_sequence_energy_dict to a pickle file with a fixed name
    with open(name +'cross' +'.pkl', 'wb') as f:
        pickle.dump(crossdick, f)

    #caffeinate.terminate()
    print('hallo')