from sequence_picking_tools import *
import pickle
import matplotlib.pyplot as plt
import numpy as np
import time
from collections import Counter



if __name__ == '__main__':
    # open the preselected prossible handle sequences as dictionary
    with open('TT_no_crosscheck10to12addmore.pkl', 'rb') as f:
        handle_energy_dict = pickle.load(f)

    handles = list(handle_energy_dict.keys())
    print(len(handles))

    crossdick = selfvalidate(handles)

    # Save the new_sequence_energy_dict to a pickle file with a fixed name
    with open('TT_no_crosscheck10to12addmorecross.pkl', 'wb') as f:
        pickle.dump(crossdick , f)
    print('hallo')