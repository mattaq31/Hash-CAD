from collections import defaultdict


class Slat:
    """
    Wrapper class to hold all of a slat's handles and related details.
    """
    def __init__(self, ID, orientation, slat_length=32):
        self.ID = ID
        self.orientation = orientation
        self.max_length = slat_length
        self.H2_handles = defaultdict(dict)
        self.H5_handles = defaultdict(dict)

    def set_handle(self, handle_id, slat_side, sequence, well, plate_name):
        if handle_id < 1 or handle_id > self.max_length:
            raise RuntimeError('Handle ID out of range')
        if slat_side == 2:
            self.H2_handles[handle_id] = {'sequence': sequence, 'well': well, 'plate': plate_name}
        elif slat_side == 5:
            self.H5_handles[handle_id] = {'sequence': sequence, 'well': well, 'plate': plate_name}
        else:
            raise RuntimeError('Wrong slat side specified (only 2 or 5 available)')



