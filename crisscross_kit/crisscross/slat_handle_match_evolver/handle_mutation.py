import numpy as np
import random
from . import apply_handle_links

def mutate_handle_arrays(slat_array, candidate_handle_arrays,
                         hallofshame, best_score_indices, unique_sequences=32,
                         memory_hallofshame=None, memory_best_parent_hallofshame=None,
                         special_hallofshame=None,
                         mutation_rate=2.0, mutation_type_probabilities=(0.425, 0.425, 0.15),
                         use_memory_type=None,
                         split_sequence_handles=False,
                         sequence_split_factor=2,
                         repeating_unit_constraints=None,
                         mutation_mask=None):
    """
    Mutates (randomizes handles) a set of candidate arrays into a new generation,
    while retaining the best scoring arrays from the previous generation.
    :param slat_array: Base slat array for design
    :param candidate_handle_arrays: Set of candidate handle arrays from previous generation
    :param hallofshame: Worst handle/antihandle combinations from previous generation
    :param best_score_indices: The indices of the best scoring arrays from the previous generation
    :param unique_sequences: Total length of handle library available
    :param memory_hallofshame: List of all the worst handle/antihandle combinations from previous generations
    :param memory_best_parent_hallofshame: List of the worst handle/antihandle combinations from previous generations (only the ones linked to the best parents)
    :param special_hallofshame: List of special handle/antihandle combinations from previous generations
    :param mutation_rate: The expected number of mutations per cycle
    :param mutation_type_probabilities: Probability of selecting a specific mutation type for a target handle/antihandle (either handle, antihandle or mixed mutations)
    :param use_memory_type: Select memory type to use for mutation selection ('off', 'all', 'best_memory', 'special')
    :param split_sequence_handles: Set to true if the handle library needs to be split between subsequent layers
    :param sequence_split_factor: The number of layers to split the handle library between (default is 2, which means a single layer would have half the available library)
    :param repeating_unit_constraints: Dictionary of handles to link together (mostly deprecated in favour of recursive algorithm in Megastructure).  Syntax is {(layer, 'top'/'bottom', (x,y)): (layer, 'top'/'bottom', (x,y))}
    :param mutation_mask: Optional integer mask to inform mutation system of any handle links in the slat design (created through recursion system)
    :return: New generation of handle arrays to be screened
    """

    # These are the arrays that will be mutated
    mutated_handle_arrays = []

    # These are the arrays that will be the mutation sources
    parent_handle_arrays = [candidate_handle_arrays[i] for i in best_score_indices]

    # these are the combinations that had the worst scores in the previous generation
    parent_hallofshame_handles = [hallofshame['handles'][i] for i in best_score_indices]
    parent_hallofshame_antihandles = [hallofshame['antihandles'][i] for i in best_score_indices]

    # number of arrays to generate
    generation_array_count = len(candidate_handle_arrays)
    parent_array_count = len(parent_handle_arrays)

    # mask to prevent the assigning of a handle in areas where none should be placed (zeros)
    mask = candidate_handle_arrays[0] > 0

    # all parents are members of the next generation and survive
    mutated_handle_arrays.extend(parent_handle_arrays)

    mutation_maps = []

    # applies a normalization just in case the input values do not sum to 1
    normalized_mutation_probabilities = [m/sum(mutation_type_probabilities) for m in mutation_type_probabilities]

    # prepares masks for each new candidate to allow mutations to occur in select areas
    for i in range(parent_array_count, generation_array_count):

        # pick someone to mutate
        pick = np.random.randint(0, parent_array_count)
        mother = parent_handle_arrays[pick].copy()
        random_choice = np.random.choice(['mutate handles', 'mutate antihandles', 'mutate anywhere'], p=normalized_mutation_probabilities)

        if random_choice == 'mutate handles':
            if use_memory_type is None or use_memory_type == 'off':
                mother_hallofshame_handles = parent_hallofshame_handles[pick]
            elif use_memory_type == 'all':
                mother_hallofshame_handles = random.sample(hallofshame['handles'] + memory_hallofshame['handles'], 1)[0]
            elif use_memory_type == 'best_memory':
                mother_hallofshame_handles = random.sample(hallofshame['handles'] + memory_best_parent_hallofshame['handles'], 1)[0]
            elif use_memory_type == 'special':
                mother_hallofshame_handles = random.sample(special_hallofshame['handles'], 1)[0]
            else:
                raise NotImplementedError

            # locates the target slats for mutation, and prepares a mask
            mask2 = np.full(candidate_handle_arrays[0].shape, False, dtype=bool)
            for layer, slatname in mother_hallofshame_handles:  # indexing has a -1 since the handles always face up (and are 1-indexed)
                mask2[:, :, layer - 1] = (slat_array[:, :, layer - 1] == slatname) | mask2[:, :, layer - 1]

        elif random_choice == 'mutate antihandles':  # or some bad antihandle sequences
            if use_memory_type is None or use_memory_type == 'off':
                mother_hallofshame_antihandles = parent_hallofshame_antihandles[pick]
            elif use_memory_type == 'all':
                mother_hallofshame_antihandles = random.sample(hallofshame['antihandles'] + memory_hallofshame['antihandles'], 1)[0]
            elif use_memory_type == 'best_memory':
                mother_hallofshame_antihandles = random.sample(hallofshame['antihandles'] + memory_best_parent_hallofshame['antihandles'], 1)[0]
            elif use_memory_type == 'special':
                mother_hallofshame_antihandles = random.sample(special_hallofshame['antihandles'], 1)[0]
            else:
                raise NotImplementedError

            # locates the target slats for mutation, and prepares a mask
            mask2 = np.full(candidate_handle_arrays[0].shape, False, dtype=bool)

            for layer, slatname in mother_hallofshame_antihandles:  # indexing has a -2 since the antihandles always face down (and are 1-indexed)
                mask2[:, :, layer - 2] = (slat_array[:, :, layer - 1] == slatname) | mask2[:, :, layer - 2]

        elif random_choice == 'mutate anywhere':
            mask2 = np.full(candidate_handle_arrays[0].shape, True, dtype=bool)

        next_gen_member = mother.copy()

        # The mutation rate is defined as the expected number of mutations in the whole structure.
        # This can be applied using Binomial and poisson statistics: [mutation rate] = [num places to be mutated] * probability
        positions_to_be_mutated = mask & mask2 # mask and mask2 are the places where mutations are allowed

        # =============================================================================
        # TWO-PHASE MUTATION WITH LINKED HANDLES
        # =============================================================================
        # When handles are linked (via phantoms, physical attachments, or explicit links),
        # mutations must be applied consistently to all linked positions.
        #
        # PHASE 1 (below): Filter mutation candidates
        #   - Use mutation_mask to identify unique mutation positions
        #   - Only allow mutations at the "first occurrence" of each link group
        #   - This prevents multiple mutations being selected for the same linked group
        #
        # PHASE 2 (after mutation): Broadcast mutations to linked positions
        #   - After mutations are applied, copy each mutated value to all positions
        #     that share the same link group (identified by equal mask values)
        #   - This ensures all linked handles get the same new value
        # =============================================================================

        # PHASE 1: Filter to unique mutation positions using link mask
        if mutation_mask is not None:

            localized_mut_mask = mutation_mask * positions_to_be_mutated # zero out positions that are not allowed to be mutated
            # Flatten, get first index of each unique value
            flat = localized_mut_mask.ravel()
            nz_idx = np.flatnonzero(flat != 0)
            # Unique non-zero values + their first occurrence indices (relative to nz_idx)
            _, first_indices = np.unique(flat[nz_idx], return_index=True)

            # Create boolean mask
            unique_mask = np.zeros_like(flat, dtype=bool)
            unique_mask[nz_idx[first_indices]] = True

            # Reshape back to original shape
            unique_mask = unique_mask.reshape(localized_mut_mask.shape)

            # apply unique mask to global positions to be mutated
            positions_to_be_mutated = positions_to_be_mutated & unique_mask

        # TODO: is this truly the best way to apply mutations?  Won't this bias towards fewer mutations if an array is not very full?
        logicforpointmutations = np.random.random(candidate_handle_arrays[0].shape) < mutation_rate / np.sum(positions_to_be_mutated)
        logicforpointmutations = logicforpointmutations & positions_to_be_mutated

        # The above can result in no mutations being applied.  In this case, set one at random.
        if np.sum(logicforpointmutations) == 0:
            # Get all valid mutation coordinates (multi-dimensional)
            possible_indices = np.argwhere(positions_to_be_mutated)
            # Randomly choose one valid coordinate
            chosen_index = tuple(possible_indices[np.random.choice(len(possible_indices))])
            # Set mutation at that coordinate
            logicforpointmutations[chosen_index] = True

        # The actual mutation happens here
        if not split_sequence_handles or slat_array.shape[2] < 3:  # just use the entire library for any one handle
            next_gen_member[logicforpointmutations] = np.random.randint(1, unique_sequences + 1, size=np.sum(logicforpointmutations))
        else:  # in the split case, only half the library is available for any one layer
            handles_per_layer = unique_sequences // sequence_split_factor
            for layer in range(logicforpointmutations.shape[2]):
                layer_index = layer % sequence_split_factor
                h_start = 1 + layer_index * handles_per_layer
                h_end = h_start + handles_per_layer
                next_gen_member[:, :, layer][logicforpointmutations[:, :, layer]] = np.random.randint(h_start, h_end, size=np.sum( logicforpointmutations[:, :, layer]))

        # PHASE 2: Broadcast mutations to all linked positions
        if mutation_mask is not None:
            # get indices of positive values in logicforpointmutations
            mutated_indices = np.argwhere(logicforpointmutations)
            # for each mutated index, find all other indices with the same mutation mask value and set them to the same handle
            for idx in mutated_indices:
                mask_value = mutation_mask[tuple(idx)]
                linked_indices = np.argwhere(mutation_mask == mask_value)
                for linked_idx in linked_indices:
                    next_gen_member[tuple(linked_idx)] = next_gen_member[tuple(idx)]

        # reapplies any handle links that were in place (this can probably be deprecated in the future)
        apply_handle_links(next_gen_member, repeating_unit_constraints)

        mutated_handle_arrays.append(next_gen_member)
        mutation_maps.append(logicforpointmutations)

    return mutated_handle_arrays, mutation_maps
