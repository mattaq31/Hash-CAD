import numpy as np


def apply_handle_links(handle_array, link_handles = {}):

    def apply_link(l1, l2, force_l1_value=False):
        handle_layer_1 = l1[0] - (2 if l1[1] == 'bottom' else 1)
        handle_layer_2 = l2[0] - (2 if l2[1] == 'bottom' else 1)

        # set the two indices to the same value (but not zero)
        if handle_array[l1[2][0], l1[2][1], handle_layer_1] == 0 and handle_array[l2[2][0], l2[2][1], handle_layer_2] == 0:
            print("Warning: Attempting to link two handles that are both zero. Skipping.")
            return

        # either force the whole linkage to be the same as position 1
        if force_l1_value and handle_array[l2[2][0], l2[2][1], handle_layer_2] != 0:
            handle_array[l2[2][0], l2[2][1], handle_layer_2] = handle_array[l1[2][0], l1[2][1], handle_layer_1]
            return
        # or just select the max value (an arbitrary selection)
        shared_handle = max(handle_array[l1[2][0], l1[2][1], handle_layer_1], handle_array[l2[2][0], l2[2][1], handle_layer_2])
        handle_array[l1[2][0], l1[2][1], handle_layer_1] = shared_handle
        handle_array[l2[2][0], l2[2][1], handle_layer_2] = shared_handle

    # applies linking i.e. ensuring two handles are the same
    for l1, l2 in link_handles.items():
        if isinstance(l2, tuple):
            apply_link(l1, l2)
        elif isinstance(l2, list):
            for l2_item in l2: # ensures they all have the same value - L1
                apply_link(l1, l2_item, force_l1_value=True)
        elif isinstance(l2, dict):
            for l2_item in l2.values(): # ensures they all have the same value - L1
                apply_link(l1, l2_item, force_l1_value=True)
        else:
            print("Warning: link_handles value is neither a tuple nor a list. Skipping.")

def generate_random_slat_handles(base_array, unique_sequences=32, link_handles = {}):
    """
    Generates an array of handles, all randomly selected.
    :param base_array: Megastructure handle positions in a 3D array
    :param unique_sequences: Number of possible handle sequences
    :param link_handles: Dictionary of handles to link together (mostly deprecated in favour of recursive algorithm in Megastructure).  Syntax is {(layer, 'top'/'bottom', (x,y)): (layer, 'top'/'bottom', (x,y))}
    :return: 2D array with handle IDs
    """

    handle_array = np.zeros((base_array.shape[0], base_array.shape[1], base_array.shape[2] - 1))
    handle_array = np.random.randint(1, unique_sequences + 1, size=handle_array.shape, dtype=np.uint16)
    for i in range(handle_array.shape[2]):
        handle_array[np.any(base_array[..., i:i + 2] == 0, axis=-1), i] = 0  # no handles where there are no slats, or no slat connections

    apply_handle_links(handle_array, link_handles)  # this function simply ensures that two handles are the same if they are linked

    return handle_array


def generate_layer_split_handles(base_array, unique_sequences=32, split_factor=2, link_handles = {}):
    """
    Generates an array of handles, with the possible ids split between each layer,
    with the goal of preventing a single slat from being self-complementary.
    :param base_array: Megastructure handle positions in a 3D array
    :param unique_sequences: Number of possible handle sequences
    :param split_factor: Number of layers to split the handle sequences between
    :param link_handles: Dictionary of handles to link together (mostly deprecated in favour of recursive algorithm in Megastructure).  Syntax is {(layer, 'top'/'bottom', (x,y)): (layer, 'top'/'bottom', (x,y))}
    :return: 2D array with handle IDs
    """


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

    return handle_array


def update_split_slat_handles(handle_array, unique_sequences=32):
    """
    Updates the split handle array with new random values inplace
    :param handle_array: Pre-populated split handle array
    :param unique_sequences: Max number of unique sequences
    :return: N/A
    """
    handle_array[handle_array > (unique_sequences / 2)] = np.random.randint(int(unique_sequences / 2) + 1, unique_sequences + 1, size=handle_array[handle_array > (unique_sequences / 2)].shape)
    handle_array[((unique_sequences / 2) >= handle_array) & (handle_array > 0)] = np.random.randint(1, int(unique_sequences / 2) + 1, size=handle_array[((unique_sequences / 2) >= handle_array) & (handle_array > 0)].shape)

def update_random_slat_handles(handle_array, unique_sequences=32):
    """
    Updates the handle array with new random values inplace
    :param handle_array: Pre-populated handle array
    :param unique_sequences: Max number of unique sequences
    :return: N/A
    """
    handle_array[handle_array > 0] = np.random.randint(1, unique_sequences + 1, size=handle_array[handle_array > 0].shape)
