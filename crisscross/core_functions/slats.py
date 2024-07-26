from collections import defaultdict
from colorama import Fore
import numpy as np


def get_slat_key(layer, slat_id):
    """
    Convenience function to generate slat key string.
    """
    return f'layer{layer}-slat{int(slat_id)}'


def convert_slat_array_into_slat_objects(slat_array):
    """
    Converts a slat array into a dictionary of slat objects for easy access.
    :param slat_array: 3D numpy array of slats - each point should either be a 0 (no slat) or a unique ID (slat here)
    :return: Dictionary of slats
    """
    slats = {}
    for layer in range(slat_array.shape[2]):
        for slat_id in np.unique(slat_array[:, :, layer]):
            if slat_id <= 0:  # removes any non-slat markers
                continue
            # slat coordinates are read in top-bottom, left-right
            slat_coords = np.argwhere(slat_array[:, :, layer] == slat_id).tolist()
            # generates a set of empty slats matching the design array
            slats[get_slat_key(layer + 1, int(slat_id))] = Slat(get_slat_key(layer + 1, int(slat_id)), layer + 1, slat_coords)
    return slats


class Slat:
    """
    Wrapper class to hold all of a slat's handles and related details.
    """
    def __init__(self, ID, layer, slat_coordinates, slat_length=32):
        self.ID = ID
        self.layer = layer
        self.max_length = slat_length
        self.reversed_slat = False  # flag to indicate if the slat has been reversed

        # converts coordinates on a 2d array to the handle number on the slat, and vice-versa
        self.slat_position_to_coordinate = {}
        self.slat_coordinate_to_position = {}
        if slat_coordinates != 'N/A':
            for index, coord in enumerate(slat_coordinates):
                self.slat_position_to_coordinate[index+1] = tuple(coord)
                self.slat_coordinate_to_position[tuple(coord)] = index + 1

        self.placeholder_list = []

        self.H2_handles = defaultdict(dict)
        self.H5_handles = defaultdict(dict)

    def reverse_direction(self):
        """
        Reverses the handle order on the slat (this should not affect the design placement of the slat).
        """
        new_slat_position_to_coordinate = {}
        new_slat_coordinate_to_position = {}
        for i in range(self.max_length):
            new_slat_position_to_coordinate[self.max_length - i] = self.slat_position_to_coordinate[i + 1]
            new_slat_coordinate_to_position[self.slat_position_to_coordinate[i + 1]] = self.max_length - i
        self.slat_position_to_coordinate = new_slat_position_to_coordinate
        self.slat_coordinate_to_position = new_slat_coordinate_to_position
        self.reversed_slat = not self.reversed_slat

    def get_sorted_handles(self, side='h2'):
        """
        Returns a sorted list of all handles on the slat (as they can be jumbled up sometimes, depending on the order they were created).
        :param side: h2 or h5
        :return: tuple of handle ID and handle dict contents
        """
        if side == 'h2':
            return sorted(self.H2_handles.items())
        elif side == 'h5':
            return sorted(self.H5_handles.items())
        else:
            raise RuntimeError('Wrong side specified (only h2 or h5 available)')

    def set_placeholder_handle(self, handle_id, slat_side, descriptor):
        """
        Assigns a placeholder to the slat, instead of a full handle.
        :param handle_id: Handle position on slat
        :param slat_side: H2 or H5
        :param descriptor: Description to use for placeholder
        :return: N/A
        """
        if handle_id < 1 or handle_id > self.max_length:
            raise RuntimeError('Handle ID out of range')

        if slat_side == 2:
            if handle_id in self.H2_handles:
                print(Fore.RED + 'WARNING: Overwriting handle %s, side 2 on slat %s' % (handle_id, self.ID))
            self.H2_handles[handle_id] = {'descriptor': descriptor}
        elif slat_side == 5:
            if handle_id in self.H5_handles:
                print(Fore.RED + 'WARNING: Overwriting handle %s, side 5 on slat %s' % (handle_id, self.ID))
            self.H5_handles[handle_id] = {'descriptor': descriptor}
        else:
            raise RuntimeError('Wrong slat side specified (only 2 or 5 available)')

        # placeholders are tracked here, for later replacement
        self.placeholder_list.append(f'handle-{handle_id}-h{slat_side}')

    def update_placeholder_handle(self,  handle_id, slat_side, sequence, well, plate_name, descriptor='No Desc.'):
        """
        Updates a placeholder handle with the actual handle.
        :param handle_id: Handle position on slat
        :param slat_side: H2 or H5
        :param sequence: Exact handle sequence
        :param well: Exact plate well
        :param plate_name: Exact plate name
        :param descriptor: Exact description of handle
        :return: N/A
        """

        input_id = f'handle-{handle_id}-h{slat_side}'
        if input_id not in self.placeholder_list:
            raise RuntimeError('Handle ID not found in placeholder list')
        else:
            self.placeholder_list.remove(input_id)

        if slat_side == 2:
            self.H2_handles[handle_id] = {'sequence': sequence, 'well': well, 'plate': plate_name,
                                          'descriptor': descriptor}
        elif slat_side == 5:
            self.H5_handles[handle_id] = {'sequence': sequence, 'well': well, 'plate': plate_name,
                                          'descriptor': descriptor}

    def set_handle(self, handle_id, slat_side, sequence, well, plate_name, descriptor='No Desc.'):
        """
        Defines the full details of a handle on a slat.
        :param handle_id: Handle position on slat
        :param slat_side: H2 or H5
        :param sequence: Exact handle sequence
        :param well: Exact plate well
        :param plate_name: Exact plate name
        :param descriptor: Exact description of handle
        :return: N/A
        """
        if handle_id < 1 or handle_id > self.max_length:
            raise RuntimeError('Handle ID out of range')
        if slat_side == 2:
            if handle_id in self.H2_handles:
                print(Fore.RED + 'WARNING: Overwriting handle %s, side 2 on slat %s' % (handle_id, self.ID))
            self.H2_handles[handle_id] = {'sequence': sequence, 'well': well, 'plate': plate_name,
                                          'descriptor': descriptor}
        elif slat_side == 5:
            if handle_id in self.H5_handles:
                print(Fore.RED + 'WARNING: Overwriting handle %s, side 5 on slat %s' % (handle_id, self.ID))
            self.H5_handles[handle_id] = {'sequence': sequence, 'well': well, 'plate': plate_name,
                                          'descriptor': descriptor}
        else:
            raise RuntimeError('Wrong slat side specified (only 2 or 5 available)')



