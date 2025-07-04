import numpy as np
import importlib

torch_spec = importlib.util.find_spec("torch")  # only imports optuna if this is available
if torch_spec is not None:
    import torch
    torch_available = True
else:
    torch_available = False

def torch_index_handles(handle_array, slat_array, handle_index_list, antihandle_index_list):
    """
    Given the original handle and slat arrays, this function extracts the handles and antihandles for the
    specified lists of handle/antihandle positions.
    :param handle_array: The handle array from which the handles and antihandles will be extracted (must be torch.tensor)
    :param slat_array: The slat array from which the slat positions will be extracted
    :param handle_index_list: List of tuples containing the slat layer, slat ID and handle layer for
    each handle slat (a single slat can have both a handle and antihandle side)
    :param antihandle_index_list: List of tuples containing the slat layer, slat ID and handle layer for
    each antihandle slat (a single slat can have both a handle and antihandle side)
    :return: Stacked tensors for both the handles and antihandles requested
    """

    def torch_extract_handle(index_list):
        for index, (slat_layer, slat_id, handle_layer) in enumerate(index_list):
            slat_indexer = (slat_array[..., slat_layer] == slat_id).nonzero(as_tuple=True)
            if index == 0:
                stacked_handles = handle_array[slat_indexer[0], slat_indexer[1], handle_layer].unsqueeze(0)
            else:
                stacked_handles = torch.cat((stacked_handles, handle_array[slat_indexer[0], slat_indexer[1], handle_layer].unsqueeze(0)))
        return stacked_handles

    stacked_handles = torch_extract_handle(handle_index_list)
    stacked_antihandles = torch_extract_handle(antihandle_index_list)

    return stacked_handles, stacked_antihandles


def torch_oneshot_hamming_compute(handles, antihandles, slat_length):
    """
    Given stacked tensors with handles and antihandles, this function computes the hamming distance between all
    possible combinations using only differentiable operations.  Processing speed is very similar to the numpy oneshot
    implementation.
    :param handles: Stacked handles tensor with shape (num_handles, slat_length)
    :param antihandles: Stacked antihandles tensor with shape (num_antihandles, slat_length)
    :param slat_length: The length of a single slat (must be an integer)
    :return: Array of results for each possible combination (a single integer per combination)
    """

    # TODO: torch gradients cannot be computed on integers.  Is this going to make memory requirements a problem?

    if not torch_available:
        raise ImportError('PyTorch is not available on this system.')

    num_handles = handles.shape[0]
    flippedhandles = torch.flip(handles, dims=[1])

    # Generate every possible shift and reversed shift of the handle sequences -
    # the goal is to simulate every possible physical interaction between two slats
    # The total length will be 4 * the slat length - 2 (two states are repeated)
    # The operations are repeated for all handles in the input array
    for i in range(slat_length):
        if i == 0:
            # first shifts (non-shifts in this case) initialize the combined tensor array
            shifted_handles = handles[:, :slat_length - i]
            shifted_handles = torch.stack((shifted_handles, flippedhandles[:, :slat_length - i]), dim=1)
        else:
            # the arrays cannot be pre-initialized as the gradient would not be computed correctly
            # torch concatenation still seems pretty fast, but could also consider using torch.scatter here
            # Normal shifts
            shifted_handles = torch.cat((shifted_handles, torch.cat((torch.zeros((handles.shape[0], i),dtype=torch.float32), handles[:, :slat_length - i]), dim=1).unsqueeze(1)), dim=1)
            shifted_handles = torch.cat((shifted_handles, torch.cat((handles[:,i:], torch.zeros((handles.shape[0], i),dtype=torch.float32)), dim=1).unsqueeze(1)), dim=1)

            # flipped shifts
            shifted_handles = torch.cat((shifted_handles, torch.cat((torch.zeros((handles.shape[0], i),dtype=torch.float32), flippedhandles[:, :slat_length - i]), dim=1).unsqueeze(1)), dim=1)
            shifted_handles = torch.cat((shifted_handles, torch.cat((flippedhandles[:,i:], torch.zeros((handles.shape[0], i),dtype=torch.float32)), dim=1).unsqueeze(1)), dim=1)

    # The antihandles should simply be tiled to generate the same number of sequences as the handles, shifts are not needed
    num_antihandles = antihandles.shape[0]
    tiled_antihandles = torch.tile(antihandles[:, np.newaxis, :], (1, (4 * slat_length) - 2, 1))

    # tiles all the handle and antihandles into a large 4D array containing:
        # all combinations of handles with antihandles (dimensions 1 and 2)
        # all possible shifts of the handles (dimension 3)
    # This final tiling ensures that each and every handle-slat is matched with each and every antihandle-slat
    combinatorial_matrix_handles = torch.tile(shifted_handles[:, torch.newaxis, :, :], (1, num_antihandles, 1, 1))
    combinatorial_matrix_antihandles = torch.tile(tiled_antihandles[torch.newaxis, :, :, :], (num_handles, 1, 1, 1))

    # After all the matches are built up, the hamming distance can be computed for all combinations in one go
    # to ensure the process is still differentiable, the sigmoid function was used to replace all boolean operations
    # 0.5 was selected as the threshold to distinguish between 0 and 1, with a large multiplier to ensure the sigmoid function is steep (i.e. close to a step function)
    all_matches = torch.sigmoid(1000000 * (0.5 - torch.abs(combinatorial_matrix_handles - combinatorial_matrix_antihandles)))

    mask_handles = combinatorial_matrix_handles == 0
    mask_antihandles = combinatorial_matrix_antihandles == 0

    all_matches = torch.where(mask_handles | mask_antihandles, torch.tensor(0.0), all_matches)

    # Sums along the specified axis
    hamming_results = slat_length - all_matches.sum(dim=3)

    return hamming_results
