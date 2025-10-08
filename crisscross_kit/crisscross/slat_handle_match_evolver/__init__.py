import numpy as np


def apply_handle_links(handle_array,link_handles = {}):

    # applies linking i.e. ensuring two handles are the same
    for l1, l2 in link_handles.items():
        handle_layer_1 = l1[0] - (2 if l1[1] == 'bottom' else 1)
        handle_layer_2 = l2[0] - (2 if l2[1] == 'bottom' else 1)

        # set the two indices to the same value (but not zero)
        if handle_array[l1[2][0], l1[2][1], handle_layer_1] == 0 and handle_array[l2[2][0], l2[2][1], handle_layer_2] == 0:
            print("Warning: Attempting to link two handles that are both zero. Skipping.")
            continue

        shared_handle = max(handle_array[l1[2][0], l1[2][1], handle_layer_1], handle_array[l2[2][0], l2[2][1], handle_layer_2])
        handle_array[l1[2][0], l1[2][1], handle_layer_1] = shared_handle
        handle_array[l2[2][0], l2[2][1], handle_layer_2] = shared_handle


def duplicate_handle_transplants(handle_array, transplant_handles = {}):

    # ensures the original slat retains a copy of the transplanted handle
    for l1, l2 in transplant_handles.items():
        handle_layer_1 = l1[0] - (2 if l1[1] == 'bottom' else 1)
        handle_layer_2 = l2[0] - (2 if l2[1] == 'bottom' else 1)
        handle_array[l1[2][0], l1[2][1], handle_layer_1] = handle_array[l2[2][0], l2[2][1], handle_layer_2]

def apply_handle_transplants(slat_array, transplant_handles={}):

    output_slat_array = slat_array.copy()
    for t1, t2 in transplant_handles.items():
        layer_1 = t1[0] - 1
        if output_slat_array[t1[2][0], t1[2][1], layer_1] == 0:
            print("Warning: Attempting to transplant a handle from a location that is zero. Skipping.")
            continue
        output_slat_array[t2[2][0], t2[2][1], layer_1] = output_slat_array[t1[2][0], t1[2][1], layer_1]
        output_slat_array[t1[2][0], t1[2][1], layer_1] = 0  # zero out the original location

    return output_slat_array

def generate_random_slat_handles(base_array, unique_sequences=32, transplant_handles={}, link_handles = {}):
    """
    Generates an array of handles, all randomly selected.
    :param base_array: Megastructure handle positions in a 3D array
    :param unique_sequences: Number of possible handle sequences
    :return: 2D array with handle IDs
    """
    base_array = apply_handle_transplants(base_array, transplant_handles) # transplants move slat coordinates to new locations so that an assembly handle can be generated for that location

    handle_array = np.zeros((base_array.shape[0], base_array.shape[1], base_array.shape[2] - 1))
    handle_array = np.random.randint(1, unique_sequences + 1, size=handle_array.shape, dtype=np.uint16)
    for i in range(handle_array.shape[2]):
        handle_array[np.any(base_array[..., i:i + 2] == 0, axis=-1), i] = 0  # no handles where there are no slats, or no slat connections

    # TODO: I think these can be combined into just one function! + need better documentation
    apply_handle_links(handle_array, link_handles)  # this one simply ensures that two handles are the same if they are linked
    duplicate_handle_transplants(handle_array, transplant_handles) # once the assembly handles have been generated, need to ensure the original slat gets a copy of the transplanted handle

    return handle_array


def generate_layer_split_handles(base_array, unique_sequences=32, split_factor=2, transplant_handles={}, link_handles = {}):
    """
    Generates an array of handles, with the possible ids split between each layer,
    with the goal of preventing a single slat from being self-complementary.
    :param base_array: Megastructure handle positions in a 3D array
    :param unique_sequences: Number of possible handle sequences
    :param split_factor: Number of layers to split the handle sequences between
    :return: 2D array with handle IDs
    """

    base_array = apply_handle_transplants(base_array, transplant_handles)

    handle_array = np.zeros((base_array.shape[0], base_array.shape[1], base_array.shape[2] - 1), dtype=np.uint16)

    if unique_sequences % split_factor != 0:
        raise ValueError("unique_sequences must be divisible by split_factor")

    handles_per_layer = unique_sequences // split_factor

    for i in range(handle_array.shape[2]):
        layer_index = i % split_factor
        h_start = 1 + layer_index * handles_per_layer
        h_end = h_start + handles_per_layer

        layer_handle_array = np.random.randint(h_start, h_end, size=(handle_array.shape[0], handle_array.shape[1]), dtype=np.uint16)
        handle_array[..., i] = layer_handle_array

    for i in range(handle_array.shape[2]):
        handle_array[np.any(base_array[..., i:i + 2] == 0, axis=-1), i] = 0  # no handles where there are no slats, or no slat connections

    apply_handle_links(handle_array, link_handles)
    duplicate_handle_transplants(handle_array, transplant_handles)

    return handle_array


# TODO: These functions also need to be updated with transplant and link handle support
def update_split_slat_handles(handle_array, unique_sequences=32):
    """
    Updates the split handle array with new random values inplace
    :param handle_array: Pre-populated split handle array
    :param unique_sequences: Max number of unique sequences
    :return: N/A
    """
    handle_array[handle_array > (unique_sequences / 2)] = np.random.randint(int(unique_sequences / 2) + 1, unique_sequences + 1, size=handle_array[handle_array > (unique_sequences / 2)].shape)
    handle_array[((unique_sequences / 2) >= handle_array) & (handle_array > 0)] = np.random.randint(1, int(unique_sequences / 2) + 1, size=handle_array[((unique_sequences / 2) >= handle_array) & (handle_array > 0)].shape)

# TODO: These functions also need to be updated with transplant and link handle support
def update_random_slat_handles(handle_array, unique_sequences=32):
    """
    Updates the handle array with new random values inplace
    :param handle_array: Pre-populated handle array
    :param unique_sequences: Max number of unique sequences
    :return: N/A
    """
    handle_array[handle_array > 0] = np.random.randint(1, unique_sequences + 1, size=handle_array[handle_array > 0].shape)
