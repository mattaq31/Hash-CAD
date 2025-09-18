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
    def __init__(self, ID, layer, slat_coordinates, non_assembly_slat=False, unique_color=None, layer_color=None):
        """
        :param ID: Slat unique ID (string)
        :param layer: Layer position for slat (normally 1 and above, but can set to 0 for special slats such as crossbars)
        :param slat_coordinates: Exact positions slat occupies on a 2D grid - either a list of tuples or a dict of lists, where the key is the handle number on the slat
        :param non_assembly_slat: If True, this slat is not used for assembly (e.g., crossbar slats)
        :param unique_color: Optional hexcode color to assign a unique color to the slat for graphics
        """
        self.ID = ID
        self.layer = layer
        self.max_length = len(slat_coordinates)
        self.non_assembly_slat = non_assembly_slat
        self.unique_color = unique_color
        self.layer_color = layer_color

        # converts coordinates on a 2d array to the handle number on the slat, and vice-versa
        self.slat_position_to_coordinate = {}
        self.slat_coordinate_to_position = {}
        if slat_coordinates != 'N/A':
            if isinstance(slat_coordinates, dict):
                for key, coord in slat_coordinates.items():
                    self.slat_position_to_coordinate[key] = tuple(coord)
                    self.slat_coordinate_to_position[tuple(coord)] = key
            else:
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

    def set_placeholder_handle(self, handle_id, slat_side, category, value, descriptor):
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
            self.H2_handles[handle_id] = {'category': category, 'value': value, 'descriptor': descriptor}
        elif slat_side == 5:
            if handle_id in self.H5_handles:
                print(Fore.RED + 'WARNING: Overwriting handle %s, side 5 on slat %s' % (handle_id, self.ID))
            self.H5_handles[handle_id] = {'category': category, 'value': value,'descriptor': descriptor}
        else:
            raise RuntimeError('Wrong slat side specified (only 2 or 5 available)')

        # placeholders are tracked here, for later replacement
        self.placeholder_list.append(f'handle|{handle_id}|h{slat_side}')

    def update_placeholder_handle(self, handle_id, slat_side, sequence, well, plate_name, category, value, concentration, descriptor='No Desc.'):
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

        input_id = f'handle|{handle_id}|h{slat_side}'
        if input_id not in self.placeholder_list:
            raise RuntimeError('Handle ID not found in placeholder list')
        else:
            self.placeholder_list.remove(input_id)

        if slat_side == 2:
            self.H2_handles[handle_id] = {'sequence': sequence, 'well': well, 'plate': plate_name,
                                          'category': category, 'value': value,
                                          'concentration':concentration,
                                          'descriptor': descriptor}
        elif slat_side == 5:
            self.H5_handles[handle_id] = {'sequence': sequence, 'well': well, 'plate': plate_name,
                                          'category': category, 'value': value,
                                          'concentration': concentration,
                                          'descriptor': descriptor}

    def set_handle(self, handle_id, slat_side, sequence, well, plate_name, category, value, concentration, descriptor='No Desc.'):
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
                                          'category': category, 'value': value,
                                          'concentration': concentration,
                                          'descriptor': descriptor}
        elif slat_side == 5:
            if handle_id in self.H5_handles:
                print(Fore.RED + 'WARNING: Overwriting handle %s, side 5 on slat %s' % (handle_id, self.ID))
            self.H5_handles[handle_id] = {'sequence': sequence, 'well': well, 'plate': plate_name,
                                          'category': category, 'value': value,
                                          'concentration': concentration,
                                          'descriptor': descriptor}
        else:
            raise RuntimeError('Wrong slat side specified (only 2 or 5 available)')

    def get_molecular_weight(self):
        """
        Calculates the molecular weight of the slat, based on the handles assigned.
        :return: Molecular weight of the slat (in Da)
        """
        total_bases = 0

        if len(self.H2_handles) < self.max_length or len(self.H5_handles) < self.max_length:
            raise RuntimeError('Not all handles have been assigned on the slat and so the MW cannot be calculated yet.')

        for handle in self.H2_handles.values():
            total_bases += len(handle['sequence'])
        for handle in self.H5_handles.values():
            total_bases += len(handle['sequence'])

        total_bases += 8064 # incorporating scaffold length
        total_bases += 5329 # incorporating length of core staples

        # Note: this calculates the molecular weight assuming individual deoxyribonucleotide monophosphates
        # - it adds an extra 18.015 g/mol for all but one base, so this value is about 6% higher than the correct value
        # Ideally we would calculate the exact molecular weight given the sequence, but this correction is good enough for now

        return total_bases * 327 - (total_bases-1) * 18.015  # 327 Da per base (on average)

