import numpy as np


def generate_random_slat_handles(base_array, unique_sequences=32):
    """
    Generates an array of handles, all randomly selected.
    :param base_array: Megastructure handle positions in a 3D array
    :param unique_sequences: Number of possible handle sequences
    :return: 2D array with handle IDs
    """
    handle_array = np.zeros((base_array.shape[0], base_array.shape[1], base_array.shape[2] - 1))
    handle_array = np.random.randint(1, unique_sequences + 1, size=handle_array.shape, dtype=np.uint16)
    for i in range(handle_array.shape[2]):
        handle_array[np.any(base_array[..., i:i + 2] == 0, axis=-1), i] = 0  # no handles where there are no slats, or no slat connections
    return handle_array


def generate_layer_split_handles(base_array, unique_sequences=32, split_factor=2):
    """
    Generates an array of handles, with the possible ids split between each layer,
    with the goal of preventing a single slat from being self-complementary.
    :param base_array: Megastructure handle positions in a 3D array
    :param unique_sequences: Number of possible handle sequences
    :param split_factor: Number of layers to split the handle sequences between
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
