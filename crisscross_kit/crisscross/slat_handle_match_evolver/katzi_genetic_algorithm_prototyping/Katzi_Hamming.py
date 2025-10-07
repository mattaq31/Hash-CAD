import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import time
from itertools import product
from tqdm import tqdm
from collections import defaultdict, OrderedDict
from crisscross.core_functions.slat_design import generate_standard_square_slats

def compute_hamming(handle_dict, antihandle_dict, valid_product_indices, slat_length):
    """
    Given a dictionary of slat handles and antihandles, this function computes the hamming distance between all possible combinations.
    :param handle_dict: Dictionary of handles i.e. {slat_id: slat_handle_array}
    :param antihandle_dict: Dictionary of antihandles i.e. {slat_id: slat_antihandle_array}
    :param valid_product_indices: A list of indices matching the possible products that should be computed (i.e. if a product is not being requested, the index should be False)
    :param slat_length: The length of a single slat (must be an integer)
    :return: Array of results for each possible combination (a single integer per combination)
    """
    single_combo = 4 * slat_length
    total_combos = single_combo * sum(valid_product_indices)
    combination_matrix_1 = np.zeros((total_combos, slat_length))
    combination_matrix_2 = np.zeros((total_combos, slat_length))
    valid_combo_index = 0
    for i, ((hk, handle_slat), (ahk, antihandle_slat)) in enumerate(product(handle_dict.items(), antihandle_dict.items())):
        if valid_product_indices[i]:
            for j in range(slat_length):
                # 4 combinations:
                # 1. X vs Y, rotation to the left
                # 2. X vs Y, rotation to the right
                # 3. X vs Y, rotation to the left, reversed X
                # 4. X vs Y, rotation to the right, reversed X
                # All rotations padded with zeros (already in array)
                # TODO: could this be sped up even further?
                combination_matrix_1[(valid_combo_index*single_combo) + j, :slat_length-j] = handle_slat[j:]
                combination_matrix_1[(valid_combo_index*single_combo) + slat_length + j, j:] = handle_slat[:slat_length-j]
                combination_matrix_1[(valid_combo_index*single_combo) + (2*slat_length) + j, :slat_length-j] = handle_slat[::-1][j:]
                combination_matrix_1[(valid_combo_index*single_combo) + (3*slat_length) + j, j:] = handle_slat[::-1][:slat_length-j]
            combination_matrix_2[valid_combo_index * single_combo:(valid_combo_index + 1) * single_combo, :] = antihandle_slat
            valid_combo_index += 1
    
    
    markedmatches = np.logical_or(combination_matrix_1 != combination_matrix_2, combination_matrix_1 == 0, combination_matrix_2 == 0)
    results = np.count_nonzero(markedmatches, axis=1)
    
    hallofshame_antihandle= combination_matrix_2[results== np.min(results)]
    hallofshame_handle= combination_matrix_1[results== np.min(results)]
    
    listofkeys = []
    for line in hallofshame_antihandle:
        
        for key, value in antihandle_dict.items():
            if np.array_equal(value, line):
                listofkeys.append(key)
                break
    listofkeys= list(set(listofkeys)) 
    return results,listofkeys,hallofshame_antihandle

def compute_hamming2(handle_dict, antihandle_dict, valid_product_indices, slat_length):
    """
    Given a dictionary of slat handles and antihandles, this function computes the hamming distance between all possible combinations.
    :param handle_dict: Dictionary of handles i.e. {slat_id: slat_handle_array}
    :param antihandle_dict: Dictionary of antihandles i.e. {slat_id: slat_antihandle_array}
    :param valid_product_indices: A list of indices matching the possible products that should be computed (i.e. if a product is not being requested, the index should be False)
    :param slat_length: The length of a single slat (must be an integer)
    :return: Array of results for each possible combination (a single integer per combination)
    """
    single_combo = 4 * slat_length
    total_combos = single_combo * sum(valid_product_indices)
    combination_matrix_1 = np.zeros((total_combos, slat_length))
    combination_matrix_2 = np.zeros((total_combos, slat_length))
    valid_combo_index = 0
    for i, ((hk, handle_slat), (ahk, antihandle_slat)) in enumerate(product(handle_dict.items(), antihandle_dict.items())):
        if valid_product_indices[i]:
            for j in range(slat_length):
                # 4 combinations:
                # 1. X vs Y, rotation to the left
                # 2. X vs Y, rotation to the right
                # 3. X vs Y, rotation to the left, reversed X
                # 4. X vs Y, rotation to the right, reversed X
                # All rotations padded with zeros (already in array)
                # TODO: could this be sped up even further?
                combination_matrix_1[(valid_combo_index*single_combo) + j, :slat_length-j] = handle_slat[j:]
                combination_matrix_1[(valid_combo_index*single_combo) + slat_length + j, j:] = handle_slat[:slat_length-j]
                combination_matrix_1[(valid_combo_index*single_combo) + (2*slat_length) + j, :slat_length-j] = handle_slat[::-1][j:]
                combination_matrix_1[(valid_combo_index*single_combo) + (3*slat_length) + j, j:] = handle_slat[::-1][:slat_length-j]
                
            combination_matrix_2[valid_combo_index * single_combo:(valid_combo_index + 1) * single_combo, :] = antihandle_slat
            valid_combo_index += 1
    results = np.count_nonzero(np.logical_or(combination_matrix_1 != combination_matrix_2, combination_matrix_1 == 0, combination_matrix_2 == 0), axis=1)
    return results,0,0


def compute_hamming3(handle_dict, antihandle_dict, valid_product_indices, slat_length):
    """
    Vectorized function to compute hamming distance between slat handle and antihandle combinations.
    """
    # Convert dictionaries to arrays
    handles = np.array(list(handle_dict.values()))
    num_handles = handles.shape[0]
    flippedhandles = handles[:,::-1]
    antihandles = np.array(list(antihandle_dict.values()))
    num_antihandles = antihandles.shape[0]
    
    # Identify valid pairs
  #  valid_pairs = np.array(valid_product_indices, dtype=bool)
    #handles = handles[valid_pairs]
    #antihandles = antihandles[valid_pairs]

    # Generate shifted and reversed versions of handles
    # Note: np.roll might be a better choice, but it wraps around which isn't wanted here, so we manually shift
    shifted_handles = np.zeros((handles.shape[0], 4 * slat_length, slat_length), dtype=np.int32)
    for i in range(slat_length):
        # Normal and reversed shifts
        shifted_handles[:, i, i:] = handles[:, :slat_length-i]
        shifted_handles[:, slat_length + i, :slat_length-i] = handles[:, i:]
        shifted_handles[:, 2 * slat_length + i, i:] =  flippedhandles[:, :slat_length-i]
        shifted_handles[:, 3 * slat_length + i, :slat_length-i] =  flippedhandles[:, i:]
    
    
        
    
    # Tile antihandles to match the expanded handle array
    tiled_antihandles = np.tile(antihandles[:, np.newaxis, :], (1, 4 * slat_length, 1))
    
    combinatorial_matrix_handles = np.tile(shifted_handles[:, np.newaxis,: ,:],(1,num_antihandles,1,1))
    combinatorial_matrix_antihandles = np.tile(tiled_antihandles[np.newaxis,:,: ,:],(num_handles,1,1,1)) 
    
    test = (combinatorial_matrix_handles == combinatorial_matrix_antihandles) & (combinatorial_matrix_handles != 0) 
    # Calculate Hamming distance (count positions where they are different and not zero)
    hamming_distances = slat_length-np.count_nonzero(test, axis=3)

    return hamming_distances  


def generate_random_slat_handles(base_array, unique_sequences=32):
    """
    Generates an array of handles, all randomly selected.
    :param base_array: Megastructure handle positions in a 3D array
    :param unique_sequences: Number of possible handle sequences
    :return: 2D array with handle IDs
    """
    handle_array = np.zeros((base_array.shape[0], base_array.shape[1], base_array.shape[2]-1))
    handle_array = np.random.randint(1, unique_sequences+1, size=handle_array.shape)
    for i in range(handle_array.shape[2]):
        handle_array[np.any(base_array[..., i:i+2] == 0, axis=-1), i] = 0  # no handles where there are no slats, or no slat connections
    return handle_array


def generate_layer_split_handles(base_array, unique_sequences=32):
    """
    Generates an array of handles, with the possible ids split between each layer,
    with the goal of preventing a single slat from being self-complementary.
    :param base_array: Megastructure handle positions in a 3D array
    :param unique_sequences: Number of possible handle sequences
    :return: 2D array with handle IDs
    """
    handle_array = np.zeros((base_array.shape[0], base_array.shape[1], base_array.shape[2]-1))

    for i in range(handle_array.shape[2]):
        if i % 2 == 0:
            h1 = 1
            h2 = int(unique_sequences/2) + 1
        else:
            h1 = int(unique_sequences/2) + 1
            h2 = unique_sequences + 1
        layer_handle_array = np.random.randint(h1, h2, size=(handle_array.shape[0], handle_array.shape[1]))
        handle_array[..., i] = layer_handle_array
    for i in range(handle_array.shape[2]):
        handle_array[np.any(base_array[..., i:i+2] == 0, axis=-1), i] = 0  # no handles where there are no slats, or no slat connections
    return handle_array


def update_split_slat_handles(handle_array, unique_sequences=32):
    """
    Updates the split handle array with new random values inplace
    :param handle_array: Pre-populated split handle array
    :param unique_sequences: Max number of unique sequences
    :return: N/A
    """
    handle_array[handle_array > (unique_sequences/2)] = np.random.randint(1, int(unique_sequences/2) + 1, size=handle_array[handle_array > (unique_sequences/2)].shape)
    handle_array[(unique_sequences / 2) >= handle_array > 0] = np.random.randint(int(unique_sequences/2) + 1, unique_sequences + 1, size=handle_array[(unique_sequences / 2) >= handle_array > 0].shape)


def update_random_slat_handles(handle_array, unique_sequences=32):
    """
    Updates the handle array with new random values inplace
    :param handle_array: Pre-populated handle array
    :param unique_sequences: Max number of unique sequences
    :return: N/A
    """
    handle_array[handle_array > 0] = np.random.randint(1, unique_sequences+1, size=handle_array[handle_array > 0].shape)
#slat_array, handle_arries, parent_arries, parent_hallofshame, hallofshame_anti_parents,
#(handle_arries, parent_arries,hallofshame_anti_parents,survivor_array, unique_sequences=32, percentofpointmutations = 0.05)
def mutate_random_slat_handles_arries(slat_array, handle_arries, parent_arries, parent_hallofshame,survivor_array, unique_sequences=32,percentofpointmutations = 0.05):
    l = len(handle_arries)
    s = len(parent_arries)
    arrsize= handle_arries[0].shape
    mask = handle_arries[0] > 0 
    fullness = np.sum(mask)/mask.size
    

    
    for i in range(1,l):
        
        pick = np.random.randint(0,s)
        mother = parent_arries[pick].copy()
       
        #pick = np.random.randint(0,s)
        #father= parent_arries[pick].copy()
        keylist_of_shame = [(tup[0]) for tup in parent_hallofshame[pick]] # could also be tup[0] no one knows
        #badparts = parent_hallofshame[pick]
        mask2 = np.isin(slat_array, keylist_of_shame)
        mask2 = mask2[..., +1:] 
        

        
        next_gen_member=mother.copy()
        
        #pick = np.random.randint(0,s)
        #targetspecificslatslogic = 
        logicforpointmutations = np.random.random(arrsize) < (percentofpointmutations/fullness)
        logicforpointmutations = logicforpointmutations & mask & mask2
        
        next_gen_member[logicforpointmutations]= np.random.randint(1, unique_sequences+1, size=np.sum(logicforpointmutations))
        
        handle_arries[i] = next_gen_member
   
        
    handle_arries[0]=survivor_array

    
    
def multi_rule_hamming(slat_array, handle_array, report_score = False, report_bad_handle_sequences = False, universal_check=True, per_layer_check=False, specific_slat_groups=None, slat_length=32):
    """
    Given a slat and handle array, this function computes the hamming distance of all handle/antihandle combinations provided.
    Scores for individual components, such as specific slat groups, can also be requested.
    :param slat_array: Array of XxYxZ dimensions, where X and Y are the dimensions of the design and Z is the number of layers in the design
    :param handle_array: Array of XxYxZ-1 dimensions containing the IDs of all the handles in the design
    :param universal_check: Set to true to provide a hamming score for the entire set of slats in the design
    :param per_layer_check: Set to true to provide a hamming score for the individual layers of the design (i.e. the interface between each layer)
    :param specific_slat_groups: Provide a dictionary, where the key is a group name and the value is a list of tuples containing the layer and slat ID of the slats in the group for which the specific hamming distance is being requested.
    :param slat_length: The length of a single slat (must be an integer)
    :return: Dictionary of scores for each of the aspects requested from the design
    """

    # identifies all slats in design
    #Katzi: Creates the list of unique slats for each layer
    unique_slats_per_layer = []
    for i in range(slat_array.shape[2]):
        slat_ids = np.unique(slat_array[:, :, i]).astype(int)
        slat_ids = slat_ids[slat_ids != 0]
        unique_slats_per_layer.append(slat_ids)

    # extracts handle values for all slats in the design
    # Katzi: Wired names bag... list of handle sequences used on the slats 
    bag_of_slat_handles = OrderedDict()
    bag_of_slat_antihandles = OrderedDict()
    score_dict = {}
    
    # Katzi: iterates over each lyer and generates the variable layer_slats which is all names of all slats in a layer
    for layer_position, layer_slats in enumerate(unique_slats_per_layer):
        
        


        # an assumption is made here that the bottom-most slat will always start with handles, then alternate to anti-handles and so on.
        
        
        # Katzi: test if we are in the 0. or the upper most layer because these layers have only one set of handles. all in between have handles and antihandles
        handles_available = True
        antihandles_available = True
        if layer_position == 0:
            handles_available = True
            antihandles_available = False
        if  layer_position == len(unique_slats_per_layer) - 1:
            handles_available = False
            antihandles_available = True
        

            
            
         # iterate over all slat names  in the layer we are in right now    
        for slat in layer_slats:
            # check if we should have handles and or antihandles and lets put them in a dictionary the keys are the tupe layer+1 of the slat and the number of the slat 
            if handles_available:
                
                # mask of the slat in the layer is slat_array[..., layer_position] == slat
                bag_of_slat_handles[(layer_position+1, slat)] = handle_array[slat_array[..., layer_position] == slat, layer_position]
            if antihandles_available:
                bag_of_slat_antihandles[(layer_position+1, slat)] = handle_array[slat_array[..., layer_position] == slat, layer_position - 1]
 
    # Katzi very mysterios code from here on lets ignore this layer pooling buisness for now
    # in the case that smaller subsets of the entire range of handle/antihandle products are required, this code snippet will remove those products that can be ignored to speed up computation
    valid_product_indices = []
    final_combination_index = 0
    layer_indices = defaultdict(list)
    group_indices = defaultdict(list)
    for i, ((hkey, handle_slat), (antihkey, antihandle_slat)) in enumerate(product(bag_of_slat_handles.items(), bag_of_slat_antihandles.items())):
        valid_product = False
        if universal_check:
            valid_product = True
        if per_layer_check and hkey[0] == antihkey[0]-1:
            valid_product = True
            layer_indices[hkey[0]].extend(range(final_combination_index*(4*slat_length), (final_combination_index+1)*(4*slat_length)))
        if specific_slat_groups:
            for group_key, group in specific_slat_groups.items():
                if hkey in group and antihkey in group:
                    group_indices[group_key].extend(range(final_combination_index*(4*slat_length), (final_combination_index+1)*(4*slat_length)))
                    valid_product = True
        if valid_product:
            final_combination_index += 1
        valid_product_indices.append(valid_product)

    # the actual hamming computation is all done here
    #t1 = time.time()
    hamming_results = compute_hamming3(bag_of_slat_handles, bag_of_slat_antihandles, valid_product_indices, slat_length)
    #print(time.time()-t1)
    # the individual scores for the components requested are computed here
    

    if universal_check:
        minhamming = np.min(hamming_results)
        score_dict['Universal'] = minhamming
        if report_score == True:
            score_dict['Universal score 1'] = np.average(hamming_results)
            score_dict['Universal score 1']
            
        if report_bad_handle_sequences == True:
            indices= np.where((hamming_results == minhamming))
            hallofshame = list(zip(indices[0], indices[1], indices[2]))
            score_dict['Hall of shame']    = hallofshame  
        
    if per_layer_check:
        for layer, indices in layer_indices.items():
            score_dict[f'Layer {layer}'] = np.min(hamming_results[indices])
    if specific_slat_groups:
        for group_key, indices in group_indices.items():
            score_dict[group_key] = np.min(hamming_results[indices])
            
    

    

    return score_dict



def generate_handle_set_and_evolve(base_array, unique_sequences=32, slat_length=32, stopat = 29, population = 150, survivors= 5 , percentofpointmutations = 0.04):
   
    
   # initiate population of handle arrays
    handle_arries=[] 
    for j in range(population):
        handle_arries.append(generate_random_slat_handles(base_array, unique_sequences)) 
        
    max_hamming_value_of_population= 0 # initialize the minimum hamming variable which is the stopping creteria
    scores= np.zeros(population) # initialize the score variable which will be used as the phenotype for the selection. i needed something which is not an integer and has a wider range
    hammings = np.zeros(population)
    hallofschame_values= []
    
    plt.ion()  # Turn on the interactive mode
    fig, ax = plt.subplots(figsize=(10, 5))
    forplotting = []
    
    while True:
        
        #analize current population individual by idividual
        for j in range(population):
            
            #hamming_dict = multi_rule_hamming(base_array, handle_array, universal_check=universal_hamming,
                                           #   per_layer_check=layer_hamming, specific_slat_groups=group_hamming,
                                            #  slat_length=slat_length)
            
            dummy = multi_rule_hamming(base_array, handle_arries[j], report_score=True, report_bad_handle_sequences=True, universal_check=True, per_layer_check=False, specific_slat_groups=None, slat_length=32)
            scores[j]= dummy['Universal score 1']#/unique_sequences
            hammings[j] = dummy['Universal']
            hallofschame_values.append( dummy['Hall of shame'])
            t=1
            
            
        #compare and find good individuals  
        max_hamming_value_of_population = np.max(hammings)
        print(max_hamming_value_of_population)
        # Find the indices of the maximum value using the explained method
        max_hamming_index_of_population = np.atleast_1d(hammings == max_hamming_value_of_population).nonzero()[0]

        #stop main loop if the desired minimum hemming deistance is found
        if max_hamming_value_of_population  >= stopat:
                break 
          
        # Get the indices of the top 'survivors' largest elements
        indices_of_largest_elements = np.argpartition(scores, -survivors)[-survivors:]

        # Get the largest elements using these indices
        largest_scores = scores[indices_of_largest_elements]
        #hallofshame_largest_elements = [hallofschame_values[i] for i in indices_of_largest_elements]
       # hallofshame_anti_parents = [halloffshame_anti[i] for i in indices_of_largest_elements]
        print(largest_scores)
        forplotting.append( np.max(largest_scores))
        # Update the plot
        ax.clear()
        ax.plot(forplotting, label='Max Score over Iterations')
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Max Score')
        ax.set_title('Max Score vs. Iteration')
        ax.legend()
        fig.canvas.draw()
        fig.canvas.flush_events()
        
        plt.pause(0.01) 
        

        
        plt.pause(0.1)  # Pause for a short time interval to see the plot update

        plt.ioff()  # Turn off interactive mode
        plt.show()  # Show the final plot
         
        


        survivor_array = handle_arries[max_hamming_index_of_population[0]]
        
        parent_arries  = [handle_arries[i].copy() for i in indices_of_largest_elements]
        
        parent_hallofshame = [hallofschame_values[i].copy() for i in indices_of_largest_elements]
        
        #evovle and update
        
        
        mutate_random_slat_handles_arries(slat_array, handle_arries, parent_arries, parent_hallofshame,survivor_array, unique_sequences=32, percentofpointmutations = percentofpointmutations)
        
        #print(hallofshame_anti_parents)
        
    return handle_arries[max_hamming_index_of_population[0]]

def generate_handle_set_and_optimize(base_array, unique_sequences=32, slat_length=32, max_rounds=30,
                                     split_sequence_handles=False, universal_hamming=True, layer_hamming=False,
                                     group_hamming=None, metric_to_optimize='Universal'):
    """
    Generates random handle sets and attempts to choose the best set based on the hamming distance between slat assembly handles.
    :param base_array: Slat position array (3D)
    :param unique_sequences: Max unique sequences in the handle array
    :param slat_length: Length of a single slat
    :param max_rounds: Maximum number of rounds to run the check
    :param split_sequence_handles: Set to true to split the handle sequences between layers evenly
    :param universal_hamming: Set to true to compute the hamming distance for the entire set of slats
    :param layer_hamming: Set to true to compute the hamming distance for the interface between each layer
    :param group_hamming: Provide a dictionary, where the key is a group name and the value is a list
    of tuples containing the layer and slat ID of the slats in the group for which the specific
    hamming distance is being requested.
    :param metric_to_optimize: The metric to optimize for (Universal, Layer X or Group ID)
    :return: 2D array with handle IDs
    """
    
    best_hamming = 0
    hammingsaver= []
    with tqdm(total=max_rounds, desc='Kinetic Trap Check') as pbar:
        for i in range(max_rounds):
            if i == 0:
                if split_sequence_handles:
                    handle_array = generate_layer_split_handles(base_array, unique_sequences)
                else:
                    handle_array = generate_random_slat_handles(base_array, unique_sequences)
                best_array = np.copy(handle_array)#
            else:
                if split_sequence_handles:
                    update_split_slat_handles(handle_array)
                else:
                    update_random_slat_handles(handle_array)

            hamming_dict = multi_rule_hamming(base_array, handle_array, universal_check=universal_hamming,
                                              per_layer_check=layer_hamming, specific_slat_groups=group_hamming,
                                              slat_length=slat_length)
            hammingsaver.append(hamming_dict['Universal'])
            if hamming_dict[metric_to_optimize] > best_hamming:
                best_hamming = hamming_dict[metric_to_optimize]
                best_array = np.copy(handle_array)
                
                
            pbar.update(1)
            pbar.set_postfix(**hamming_dict)
    print('Optimization complete - final best hamming distance: %s' % best_hamming)
    return best_array


if __name__ == '__main__':
    
    os.environ["OPENBLAS_NUM_THREADS"] = "12"
    
    slat_array, unique_slats_per_layer = generate_standard_square_slats(32)  # standard square
    
    # reads in and formats slat design into a 3D array
    output_folder= "C:/Users/Flori/Crisscross-Design"
    design_file= "layer_arrays.xlsx"
    design_df = pd.read_excel(os.path.join(output_folder, design_file), sheet_name=None, header=None)
    slat_array = np.zeros((design_df['Layer_0'].shape[0], design_df['Layer_0'].shape[1], len(design_df)))
    for i, key in enumerate(design_df.keys()):
        slat_array[..., i] = design_df[key].values

        slat_array[slat_array == -1] = 0  # removes the seed values, will re-add them later
    
    slat_array, unique_slats_per_layer = generate_standard_square_slats(32)  # standard square
    handle_array = generate_random_slat_handles(slat_array, 32)
    #hamming_dict = multi_rule_hamming(slat_array, handle_array, report_score=True, universal_check=True)
    ergebniss = generate_handle_set_and_evolve(base_array= slat_array)
    
    #result = generate_handle_set_and_optimize(slat_array, max_rounds=30)
    

    
   