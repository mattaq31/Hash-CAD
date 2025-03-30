import numpy as np


def mutate_handle_arrays(slat_array, candidate_handle_arrays,
                         hallofshame_handles, hallofshame_antihandles,
                         best_score_indices, unique_sequences=32,
                         mutation_rate=1.0, mutation_type_probabilities=(0.425, 0.425, 0.15),
                         split_sequence_handles=False):
    """
    Mutates (randomizes handles) a set of candidate arrays into a new generation,
    while retaining the best scoring arrays  from the previous generation.
    :param slat_array: Base slat array for design
    :param candidate_handle_arrays: Set of candidate handle arrays from previous generation
    :param hallofshame_handles: Worst handle combinations from previous generation
    :param hallofshame_antihandles: Worst antihandle combinations from previous generation
    :param best_score_indices: The indices of the best scoring arrays from the previous generation
    :param unique_sequences: Total length of handle library available
    :param mutation_rate: If a handle is selected for mutation, the probability that it will be changed
    :param mutation_type_probabilities: Probability of selecting a specific mutation type for a target handle/antihandle
    (either handle, antihandle or mixed mutations)
    :param split_sequence_handles: Set to true if the handle library needs to be split between subsequent layers
    :return: New generation of handle arrays to be screened
    """

    # These are the arrays that will be mutated
    mutated_handle_arrays = []

    # These are the arrays that will be the mutation sources
    parent_handle_arrays = [candidate_handle_arrays[i] for i in best_score_indices]

    # these are the combinations that had the worst scores in the previous generation
    parent_hallofshame_handles = [hallofshame_handles[i] for i in best_score_indices]
    parent_hallofshame_antihandles = [hallofshame_antihandles[i] for i in best_score_indices]

    # number of arrays to generate
    generation_array_count = len(candidate_handle_arrays)
    parent_array_count = len(parent_handle_arrays)

    # mask to prevent the assigning of a handle in areas where none should be placed (zeros)
    mask = candidate_handle_arrays[0] > 0

    # all parents are members of the next generation and survive
    mutated_handle_arrays.extend(parent_handle_arrays)

    mutation_maps = []
    # prepares masks for each new candidate to allow mutations to occur in select areas
    for i in range(parent_array_count, generation_array_count):

        # pick someone to mutate
        pick = np.random.randint(0, parent_array_count)
        mother = parent_handle_arrays[pick].copy()
        random_choice = np.random.choice(['mutate handles', 'mutate antihandles', 'mutate anywhere'],
                                         p=mutation_type_probabilities)

        if random_choice == 'mutate handles':

            mother_hallofshame_handles = parent_hallofshame_handles[pick]

            # locates the target slats for mutation, and prepares a mask
            mask2 = np.full(candidate_handle_arrays[0].shape, False, dtype=bool)
            for layer, slatname in mother_hallofshame_handles:  # indexing has a -1 since the handles always face up (and are 1-indexed)
                mask2[:, :, layer - 1] = (slat_array[:, :, layer - 1] == slatname) | mask2[:, :, layer - 1]

        elif random_choice == 'mutate antihandles':  # or some bad antihandle sequences
            mother_hallofshame_antihandles = parent_hallofshame_antihandles[pick]

            # locates the target slats for mutation, and prepares a mask
            mask2 = np.full(candidate_handle_arrays[0].shape, False, dtype=bool)

            for layer, slatname in mother_hallofshame_antihandles:  # indexing has a -2 since the antihandles always face down (and are 1-indexed)
                mask2[:, :, layer - 2] = ((slat_array[:, :, layer - 2] == slatname)) | mask2[:, :, layer - 2]

        elif random_choice == 'mutate anywhere':
            mask2 = np.full(candidate_handle_arrays[0].shape, True, dtype=bool)

        next_gen_member = mother.copy()
        # This fills an array with true values at random locations with the probability of mutationrate at each location
        # Mask and mask2 two are the places where mutations are allowed
        logicforpointmutations = np.random.random(candidate_handle_arrays[0].shape) < mutation_rate
        logicforpointmutations = logicforpointmutations & mask & mask2

        # The actual mutation happens here
        if not split_sequence_handles:  # just use the entire library for any one handle
            next_gen_member[logicforpointmutations] = np.random.randint(1, unique_sequences + 1, size=np.sum(logicforpointmutations))
        else:  # in the split case, only half the library is available for any one layer
            for layer in range(logicforpointmutations.shape[2]):
                if layer % 2 == 0:
                    h1 = 1
                    h2 = int(unique_sequences / 2) + 1
                else:
                    h1 = int(unique_sequences / 2) + 1
                    h2 = unique_sequences + 1

                next_gen_member[:, :, layer][logicforpointmutations[:, :, layer]] = np.random.randint(h1, h2, size=np.sum( logicforpointmutations[:, :, layer]))
        mutated_handle_arrays.append(next_gen_member)
        mutation_maps.append(logicforpointmutations)

    return mutated_handle_arrays, mutation_maps
