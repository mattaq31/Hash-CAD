from collections import defaultdict
from colorama import Fore


class Slat:
    """
    Wrapper class to hold all of a slat's handles and related details.
    """
    def __init__(self, ID, layer, slat_coordinates, slat_length=32):
        self.ID = ID
        self.layer = layer
        self.max_length = slat_length

        # converts coordinates on a 2d array to the handle number on the slat, and vice-versa
        self.slat_position_to_coordinate = {}
        self.slat_coordinate_to_position = {}
        if slat_coordinates != 'N/A':
            for index, coord in enumerate(slat_coordinates):
                self.slat_position_to_coordinate[index+1] = tuple(coord)
                self.slat_coordinate_to_position[tuple(coord)] = index + 1

        self.H2_handles = defaultdict(dict)
        self.H5_handles = defaultdict(dict)

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

    def set_handle(self, handle_id, slat_side, sequence, well, plate_name, descriptor='No Desc.'):
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



