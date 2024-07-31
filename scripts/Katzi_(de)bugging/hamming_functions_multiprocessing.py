import numpy as np
from itertools import product
from tqdm import tqdm
from collections import defaultdict, OrderedDict
import matplotlib.pyplot as plt
import multiprocessing
from crisscross.core_functions.slat_design import generate_standard_square_slats
import pandas as pd
import os
import time






#compute_hamming(bag_of_slat_handles, bag_of_slat_antihandles, valid_product_indices, slat_length)
def compute_hamming(handle_dict, antihandle_dict, valid_product_indices, slat_length):
    """
    Given a dictionary of slat handles and antihandles, this function computes the hamming distance between all possible combinations.
    :param handle_dict: Dictionary of handles i.e. {slat_id: slat_handle_array}
    :param antihandle_dict: Dictionary of antihandles i.e. {slat_id: slat_antihandle_array}
    :param valid_product_indices: A list of indices matching the possible products that should be computed (i.e. if a product is not being requested, the index should be False)
    :param slat_length: The length of a single slat (must be an integer)
    :return: Array of results for each possible combination (a single integer per combination)
    """
    """
    Vectorized function to compute hamming distance between slat handle and antihandle combinations.
    """

    # Convert dictionaries to arrays for faster computations
    handles = np.array(list(handle_dict.values()))
    num_handles = handles.shape[0]
    flippedhandles = handles[:,::-1]
    antihandles = np.array(list(antihandle_dict.values()))
    num_antihandles = antihandles.shape[0]
    
    # Identify valid pairs 
    # Variable is here for legacy Futur implementations of this will be done outside the function


    # Generate shifted and reversed versions of handles
    # Generate and array of the slat handle array shiftet relative to the antihandle array for all possible shifts. 
    shifted_handles = np.zeros((handles.shape[0], 4 * slat_length, slat_length), dtype=np.int32)
    for i in range(slat_length):
        # Normal and reversed shifts
        shifted_handles[:, i, i:] = handles[:, :slat_length-i]
        shifted_handles[:, slat_length + i, :slat_length-i] = handles[:, i:]
        shifted_handles[:, 2 * slat_length + i, i:] =  flippedhandles[:, :slat_length-i]
        shifted_handles[:, 3 * slat_length + i, :slat_length-i] =  flippedhandles[:, i:]
    
    
    # Here the array and the reverse array appeare twice in the matrix which is not so nice 

    # Tile antihandles to match the expanded handle array
    tiled_antihandles = np.tile(antihandles[:, np.newaxis, :], (1, 4 * slat_length, 1))

    # The stuff what follows is hard to grasp. It is base on the idea that the product of a vector and a transposed vector contains all combination of both of them. 
    #Furthe such an operation can be computed with numeric efficientcy by copyig the array itself several times and uising the standar hadamard product implementation in numpy. 
    # Note: we are not computing products but and and operation. But that does not realy matter
    combinatorial_matrix_handles = np.tile(shifted_handles[:, np.newaxis,: ,:],(1,num_antihandles,1,1))
    combinatorial_matrix_antihandles = np.tile(tiled_antihandles[np.newaxis,:,: ,:],(num_handles,1,1,1)) 

    # find all the places where a handle and an antihandle match
    all_matches = (combinatorial_matrix_handles == combinatorial_matrix_antihandles) & (combinatorial_matrix_handles != 0) 
    # Calculate Hamming distance (count positions where they are different and not zero)

    
    hamming_distances = slat_length-np.count_nonzero(all_matches, axis=3)
    
    # Short explanantion: the Array hamming_distances has 3 dimesions 1,2,3  the 1. is for the name of a antihanlde sequend, the second is and handle sequence. and the the name of the binding mode i.e the configuration of binding. The value in the array is the number of bound sequences in it
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


def process_handle(index, handle_array, base_array, report_score, report_bad_handle_sequences, universal_check, per_layer_check, specific_slat_groups, slat_length):
    # Call the function with dynamic arguments
    result = multi_rule_hamming(base_array, handle_array, report_score=report_score, 
                                report_bad_handle_sequences=report_bad_handle_sequences, 
                                universal_check=universal_check, per_layer_check=per_layer_check, 
                                specific_slat_groups=specific_slat_groups, slat_length=slat_length)
    # Prepare the output depending on what is reported
    output = [index]
    if report_score:
        output.append(result.get('Score 1', None))
    output.append(result.get('Universal', None))
    if report_bad_handle_sequences:
        output.extend([result.get('Hall of shame handles', None), result.get('Hall of shame antihandles', None)])
    return output

def multi_rule_hamming(slat_array, handle_array, report_score = True, report_bad_handle_sequences = True, universal_check=True, per_layer_check=False, specific_slat_groups=None, slat_length=32):
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
    
    slat_array = np.array(slat_array, dtype=np.uint8)
    handle_array = np.array(handle_array, dtype=np.uint8)
    # identifies all slats in design
    #Katzi: Creates the list of all slats present in a layer
    unique_slats_per_layer = []
    for i in range(slat_array.shape[2]):
        slat_ids = np.unique(slat_array[:, :, i]).astype(int)
        slat_ids = slat_ids[slat_ids != 0]
        unique_slats_per_layer.append(slat_ids)

    # extracts handle values for all slats in the design
    # Katzi: These dictionaries will contain all handles and a key value which contains the layer and the name of the handle. Note that handles and antihandles are only unique within a layer
    handle_dict = OrderedDict()
    antihandle_dict = OrderedDict()
    #This will be a dictionary where all scores are saved 
    score_dict = {}
    
    # This will fill the dictinaries
    # Katzi: iterates over each layer and generates the variable layer_slats which is all names of all slats in a layer
    for layer_position, layer_slats in enumerate(unique_slats_per_layer):
        
        # an assumption is made here that the bottom-most slat will always start with handles, then alternate to anti-handles and so on.
        # Katzi: this checks if we are in the 0. or the upper most layer because these layers have only one set of handles. all in between have handles and antihandles
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
                handle_dict[(layer_position+1, slat)] = handle_array[slat_array[..., layer_position] == slat, layer_position]
            if antihandles_available:
                antihandle_dict[(layer_position+1, slat)] = handle_array[slat_array[..., layer_position] == slat, layer_position - 1]
    #

    # in the case that smaller subsets of the entire range of handle/antihandle products are required, this code snippet will remove those products that can be ignored to speed up computation
    valid_product_indices = []
    final_combination_index = 0
    layer_indices = defaultdict(list)
    group_indices = defaultdict(list)
    for i, ((hkey, handle_slat), (antihkey, antihandle_slat)) in enumerate(product(handle_dict.items(), antihandle_dict.items())):
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
    # The stuff bellow was once part of a function that was called only here. I removed the funvtion sinvce this made the multiprocessingh slower ( I have no clue why this is )
    handles = np.array(list(handle_dict.values()))
    num_handles = handles.shape[0]
    flippedhandles = handles[:,::-1]
    antihandles = np.array(list(antihandle_dict.values()))
    num_antihandles = antihandles.shape[0]
    
    # Generate shifted and reversed versions of handles
    # Generate and array of the slat handle array shiftet relative to the antihandle array for all possible shifts. 
    shifted_handles = np.zeros((handles.shape[0], 4 * slat_length, slat_length), dtype=np.uint8)
    for i in range(slat_length):
        # Normal and reversed shifts
        shifted_handles[:, i, i:] = handles[:, :slat_length-i]
        shifted_handles[:, slat_length + i, :slat_length-i] = handles[:, i:]
        shifted_handles[:, 2 * slat_length + i, i:] =  flippedhandles[:, :slat_length-i]
        shifted_handles[:, 3 * slat_length + i, :slat_length-i] =  flippedhandles[:, i:]
    
    
    # Here the array and the reverse array appeare twice in the matrix which is not so nice 

    # Tile antihandles to match the expanded handle array
    tiled_antihandles = np.tile(antihandles[:, np.newaxis, :], (1, 4 * slat_length, 1))

    # The stuff what follows is hard to grasp. It is base on the idea that the product of a vector and a transposed vector contains all combination of both of them. 
    #Furthe such an operation can be computed with numeric efficientcy by copyig the array itself several times and uising the standar hadamard product implementation in numpy. 
    # Note: we are not computing products but and and operation. But that does not realy matter

    combinatorial_matrix_handles = np.tile(shifted_handles[:, np.newaxis,: ,:],(1,num_antihandles,1,1))

    combinatorial_matrix_antihandles = np.tile(tiled_antihandles[np.newaxis,:,: ,:],(num_handles,1,1,1)) 


    # find all the places where a handle and an antihandle match
    all_matches = (combinatorial_matrix_handles == combinatorial_matrix_antihandles) & (combinatorial_matrix_handles != 0) 
    # Calculate Hamming distance (count positions where they are different and not zero)

    
    hamming_results = slat_length-np.count_nonzero(all_matches, axis=3)
    # the individual scores for the components requested are computed here
    

    if universal_check:
        minhamming = np.min(hamming_results)
        score_dict['Universal'] = minhamming
 
        
    if per_layer_check:
        for layer, indices in layer_indices.items():
            score_dict[f'Layer {layer}'] = np.min(hamming_results[indices])
    if specific_slat_groups:
        for group_key, indices in group_indices.items():
            score_dict[group_key] = np.min(hamming_results[indices])
            
            
     #        
    if report_score == True:
                # This is motivated by the definition of the partition function in the dirks2007 (original nupack paper)
                score_dict['Score 1'] = -np.average( np.exp(-10*(hamming_results-slat_length)))
               # hamming_results-slat_length is the number of matches 
       
               # If wanted All the indices where the hamming distance was the samllest is reporte. This will be used for mutations later. These are the handle sequences to be eliminated
    if report_bad_handle_sequences == True:
                indices= np.where((hamming_results == minhamming))
                #hallofshame = list(zip(indices[0], indices[1], indices[2]))
                hallofshamehandles = [list(handle_dict.keys())[i] for i in indices[0]]
                hallofshameantihandles = [list(antihandle_dict.keys())[i] for i in indices[1]]
                score_dict['Hall of shame handles']    = hallofshamehandles
                score_dict['Hall of shame antihandles']    = hallofshameantihandles 
                
                
                
    

    

    return score_dict

def generate_handle_set_and_evolve(base_array, unique_sequences=32, slat_length=32, stopat = 28, population =30, survivors=3 , percentofpointmutations = 0.0025, generations = 20, split_sequence_handles=True):
   
    
   # initiate population of handle arrays
    handle_arries=[] 
    if split_sequence_handles == False:
        for j in range(population):
            handle_arries.append(generate_random_slat_handles(base_array, unique_sequences)) 
    else:
        for j in range(population):
            handle_arries.append(generate_layer_split_handles(base_array, unique_sequences)) 
        
    #handle_arries[0] = np.load('glider_16eachlayer_longrund.npy')
    #handle_arries[0] = create_hamming_31_square_handles()
    max_hamming_value_of_population= 0 # initialize the minimum hamming variable which is the stopping creteria
    scores= np.zeros(population) # initialize the score variable which will be used as the phenotype for the selection.
    hammings = np.zeros(population)
    hallofschame_Hvalues= []
    hallofschame_AHvalues= []
    
    plt.ion()  # Turn on the interactive mode
    fig, ax = plt.subplots(figsize=(10, 5))
    forplotting = []
     # These are the settings for the hamming distance computattion which are essential for the evolver. So I hardcodet them here
    settings = {
    'report_score': True,
    'report_bad_handle_sequences': True,
    'universal_check': True,
    'per_layer_check': False,
    'specific_slat_groups': None,
    'slat_length': slat_length
}
    
    

    # This is the main game/evolution loop where generations are created, evaluated, and mutated
    for ever in range(generations):
        
        #analize current population individual by idividual and gather reports of the scores and the bad handles of each
        # Setup multiprocessing to handle tasks
        start = time.time()
        # uset 67 percent of the cors available on the computer ( otherwise it might crash)
        num_processes = max(1, int(multiprocessing.cpu_count()/1.5))
        with multiprocessing.Pool(processes=num_processes) as pool:
            results = pool.starmap(process_handle, [(j, handle_arries[j], base_array) + tuple(settings.values()) for j in range(population)])
    
        # Unpack and store results from multiprocessing
        for res in results:
            index = res[0]
            offset = 1
            if settings['report_score']:
                scores[index] = res[offset]
                offset += 1
            hammings[index] = res[offset]
            offset += 1
            if settings['report_bad_handle_sequences']:
                hallofschame_Hvalues.append(res[offset])
                hallofschame_AHvalues.append(res[offset + 1]) 
        end = time.time()
        print ( end- start)   
            
        #compare and find the individual with the best hamming distance i.e. the larges one. Note: there might be several 
        max_hamming_value_of_population = np.max(hammings)
        print(max_hamming_value_of_population)
        
        # Find the indices of the maximum value. Note there might be several but we only need one therefor we pick one 
        #max_hamming_index_of_population = np.atleast_1d(hammings == max_hamming_value_of_population).nonzero()[0]

        #stop main loop if the desired minimum hemming deistance is found already
        #if max_hamming_value_of_population  >= stopat:
               # break 
        
            
        
        
        # Get the indices of the top 'survivors' largest elements
        indices_of_largest_scores = np.argpartition(scores, -survivors)[-survivors:]
        
        # Sort the indices based on the scores to get the largest scores in descending order
        sorted_indices_of_largest_scores = indices_of_largest_scores[np.argsort(-scores[indices_of_largest_scores])]
        
        # Get the largest elements using the sorted indices
        largest_scores = scores[sorted_indices_of_largest_scores]
        
        
        

        print(largest_scores)
        
        # just the plotting here....
        forplotting.append( -np.max(largest_scores))
        # Update the plot
        ax.clear()
        ax.plot(forplotting, label='Max Score over Iterations')
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Max Score')
        ax.set_yscale('log')
        ax.set_title('Max Score vs. Iteration')
        ax.legend()
        fig.canvas.draw()
        fig.canvas.flush_events()
        
        plt.pause(0.01) 
        

        
        plt.pause(0.1)  # Pause for a short time interval to see the plot update

        plt.ioff()  # Turn off interactive mode
        plt.show()  # Show the final plot
         
        
        
        
        # These are the arrays that will be mutated
        parent_arries  = [handle_arries[i].copy() for i in indices_of_largest_scores]
        
        parent_hallofshame_handles = [hallofschame_Hvalues[i].copy() for i in indices_of_largest_scores]
        parent_hallofshame_antihandles = [hallofschame_AHvalues[i].copy() for i in indices_of_largest_scores]
        #evovle and update
        

        mutate_random_slat_handles_arries(slat_array, handle_arries, parent_arries, parent_hallofshame_handles , parent_hallofshame_antihandles, unique_sequences=unique_sequences, percentofpointmutations = percentofpointmutations, split_sequence_handles=split_sequence_handles)


        #print(hallofshame_anti_parents)
        
    return handle_arries[sorted_indices_of_largest_scores[0]]

def mutate_random_slat_handles_arries(slat_array, handle_arries, parent_arries, parent_hallofshame_handles, parent_hallofshame_antihandles, unique_sequences=32,percentofpointmutations = 1, split_sequence_handles= False):
    
    # This function writes direclty into the handle_arries
    
    # number of arries to gnerate
    l = len(handle_arries)
    # number of parents which can be mutated
    s = len(parent_arries)
    arrsize= handle_arries[0].shape
    
    # a mask that provides the allowed places for mutations since some of these arries have zeros in them because they have the other non black geometry
    mask = handle_arries[0] > 0 
    fullness = np.sum(mask)
    
    # increase mutation rate occansionally


    
    # all parents are members of the next generation and survive
    for i in range(0,s):
        handle_arries[i] = parent_arries[i]

    # do the mutations
    for i in range(s,l):
        mutationrate = percentofpointmutations
        # pick someone to mutate
        pick = np.random.randint(0,s)
        mother = parent_arries[pick].copy()
        
        random_choice = np.random.choice(['mutate Handles', 'mutate Antihandles', 'mutate everywhere'], p=[0.425, 0.425, 0.15])
        if  random_choice == 'mutate Handles':
       
            mother_hallofshame_handles= parent_hallofshame_handles[pick]
    
    
            
            # locates the bad slats
            #eylist_of_shame = [(tup[1]) for tup in parent_hallofshame[pick]] # could also be tup[1] no one knows
            false_array_3d = np.full(slat_array.shape, False, dtype=bool)
            
            for layer, slatname in mother_hallofshame_handles:
                false_array_3d[ : , :, layer-1] = ((slat_array[ : , :, layer-1] == slatname) ) | false_array_3d[ : , :, layer-1] 
                
            #this is handles
            mask2 = false_array_3d[:,:,:-1]
        elif random_choice == 'mutate Antihandles': # or some bad antihandle sequences
            mother_hallofshame_antihandles= parent_hallofshame_antihandles[pick]
    
    
            
            # locates the bad slats
            #eylist_of_shame = [(tup[1]) for tup in parent_hallofshame[pick]] # could also be tup[1] no one knows
            false_array_3d = np.full(slat_array.shape, False, dtype=bool)
            
            for layer, slatname in mother_hallofshame_antihandles:
                false_array_3d[ : , :, layer-1] = ((slat_array[ : , :, layer-1] == slatname) ) | false_array_3d[ : , :, layer-1] 
                
            #this is handles
            mask2 = false_array_3d[:,:,+1:]
        elif  random_choice == 'mutate everywhere':
            
             mask2 = np.full(slat_array.shape, True, dtype=bool)
             mask2 = mask2[:,:,+1:]
             mutationrate = percentofpointmutations  * 32*5/fullness
       # mask2 = mask2[..., +1:] 
        # put some random mutations occansionally

        
        next_gen_member=mother.copy()
        
        #pick = np.random.randint(0,s)
        #This is a bit hard to understand but this fills an array with true values at random locations with the probability of  percentofpointmutations/fullness at each location
        # Here I select allowed locations for point mutations. mask and mask2 two are the places where mutations are allowed
        logicforpointmutations = np.random.random(arrsize) < (percentofpointmutations)
        logicforpointmutations = logicforpointmutations & mask & mask2
        # This is tha actual mutating We need to chekc if we split the sequences 16 to 16 for even and odd layers or not 
        if split_sequence_handles == False:
            next_gen_member[logicforpointmutations]= np.random.randint(1, unique_sequences+1, size=np.sum(logicforpointmutations))
        else:
            for layer in range(logicforpointmutations.shape[2]):
                if layer % 2 == 0:
                    h1 = 1
                    h2 = int(unique_sequences/2) + 1
                else:
                    h1 = int(unique_sequences/2) + 1
                    h2 = unique_sequences + 1
                
                next_gen_member[:,:,layer][logicforpointmutations[:,:,layer]] = np.random.randint(h1, h2, size=np.sum(logicforpointmutations[:,:,layer]))
        handle_arries[i] = next_gen_member
   
        
    #
    



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
    with tqdm(total=max_rounds, desc='Kinetic Trap Check') as pbar:
        for i in range(max_rounds):
            if i == 0:
                if split_sequence_handles:
                    handle_array = generate_layer_split_handles(base_array, unique_sequences)
                else:
                    handle_array = generate_random_slat_handles(base_array, unique_sequences)
                best_array = np.copy(handle_array)
            else:
                if split_sequence_handles:
                    update_split_slat_handles(handle_array)
                else:
                    update_random_slat_handles(handle_array)

            hamming_dict = multi_rule_hamming(base_array, handle_array, universal_check=universal_hamming,
                                              per_layer_check=layer_hamming, specific_slat_groups=group_hamming,
                                              slat_length=slat_length)
            if hamming_dict[metric_to_optimize] > best_hamming:
                best_hamming = hamming_dict[metric_to_optimize]
                best_array = np.copy(handle_array)
            pbar.update(1)
            pbar.set_postfix(**hamming_dict)
    print('Optimization complete - final best hamming distance: %s' % best_hamming)
    return best_array



def create_hamming_31_square_handles():
    # Create an empty 32x32 array
    array = np.zeros((32, 32, 1), dtype=np.int32)

    # Fill each row with the corresponding value (1 to 32)
    for i in range(32):
        array[i, :, 0] = i + 1

    return array

if __name__ == '__main__':
    
   # slat_array, unique_slats_per_layer = generate_standard_square_slats(32)  # standard square
   
    #handle_array = generate_random_slat_handles(slat_array, 32)
#hamming_dict = multi_rule_hamming(slat_array, handle_array, report_score=True, universal_check=True)
   # ergebniss = generate_handle_set_and_evolve(base_array= slat_array)
    #os.environ["OPENBLAS_NUM_THREADS"] = "12"
    output_folder= "C:/Users/Flori/Crisscross-Design"
    design_file= "layer_arrays.xlsx"
    design_df = pd.read_excel(os.path.join(output_folder, design_file), sheet_name=None, header=None)
    slat_array = np.zeros((design_df['Layer_0'].shape[0], design_df['Layer_0'].shape[1], len(design_df)))
    for i, key in enumerate(design_df.keys()):
        slat_array[..., i] = design_df[key].values

        slat_array[slat_array == -1] = 0  # removes the seed values, will re-add them later
    
    slat_array, unique_slats_per_layer = generate_standard_square_slats(32)  # standard square
    handle_array = generate_random_slat_handles(slat_array, 32)
    result = generate_handle_set_and_optimize(slat_array, max_rounds=30)
    ergebnüsse= generate_handle_set_and_evolve(base_array= slat_array,unique_sequences= 32,  stopat = 28, population =300, survivors=5 ,percentofpointmutations = 0.03, generations=20, split_sequence_handles=False)
    
    