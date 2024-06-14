import numpy as np
from crisscross.core_functions.slats import Slat
from colorama import Fore, Back


class Megastructure:
    """
    Convenience class that bundles the entire details of a megastructure including slat positions, seed handles and cargo.
    """
    def __init__(self, slat_array, layer_interface_orientations=None):
        """
        :param slat_array: Array of slat positions (3D - X,Y, layer ID) containing the positions of all slats in the design.
        :param layer_interface_orientations: The direction each slat will be facing in the design.
        E.g. for a 2 layer design, [2, 5, 2] implies that the bottom layer will have H2 handles sticking out,
        the connecting interface will have H5 handles and the top layer will have H2 handles again.
        TODO: how to enforce slat length?  Will this need to change in the future?
        TODO: how do we consider the additional 12nm/6nm on either end of the slat?
        """
        self.slat_array = slat_array
        self.handle_arrays = None
        self.slats = {}
        self.num_layers = slat_array.shape[2]

        # if no custom interface supplied, assuming alternating H2/H5 handles,
        # with H2 at the bottom, H5 at the top, and alternating connections in between
        # e.g. for a 3-layer structure, layer_interface_orientations = [2, (5, 2), (5,2), 5]
        if not layer_interface_orientations:
            self.layer_interface_orientations = [2] + [(5, 2)] * (self.num_layers-1) + [5]
        else:
            self.layer_interface_orientations = layer_interface_orientations

        for layer in range(self.num_layers):
            for slat_id in np.unique(slat_array[:, :, layer]):
                if slat_id <= 0:  # removes any non-slat markers
                    continue
                # slat coordinates are read in top-bottom, left-right
                slat_coords = np.argwhere(slat_array[:, :, layer] == slat_id).tolist()
                # generates a set of empty slats matching the design array
                self.slats[self.get_slat_key(layer + 1, int(slat_id))] = Slat(
                    self.get_slat_key(layer + 1, int(slat_id)), layer + 1, slat_coords)

    @staticmethod
    def get_slat_key(layer, slat_id):
        """
        Convenience function to generate slat key string.
        """
        return f'layer{layer}-slat{int(slat_id)}'

    def assign_crisscross_handles(self, handle_arrays, crisscross_handle_plates, crisscross_antihandle_plates):
        """
        Assigns crisscross handles to the slats based on the handle arrays provided.
        :param handle_arrays: 3D array of handle values (X, Y, layer) where each value corresponds to a handle ID.
        :param crisscross_handle_plates: Crisscross handle plates.
        :param crisscross_antihandle_plates: Crisscross anti-handle plates.
        TODO: this function assumes the pattern is always handle -> antihandle -> handle -> antihandle etc.
        Can we make this customizable?
        :return: N/A
        """

        if handle_arrays.shape[2] != self.num_layers - 1:
            raise RuntimeError('Need to specify the correct number of layers when assigning crisscross handles.')

        self.handle_arrays = handle_arrays

        for key, slat in self.slats.items():
            slat_crisscross_interfaces = []
            handle_layers = []
            handle_plates = []
            if slat.layer == 1:  # only one interface since slat is at the bottom of the stack
                slat_crisscross_interfaces.append(self.layer_interface_orientations[1][0])
                handle_layers.append(0)
                handle_plates.append(crisscross_handle_plates)
            elif slat.layer == self.num_layers:  # only one interface since slat is at the top of the stack
                slat_crisscross_interfaces.append(self.layer_interface_orientations[-2][1])
                handle_layers.append(-1)
                handle_plates.append(crisscross_antihandle_plates)
            else:  # two interfaces otherwise
                slat_crisscross_interfaces.extend([self.layer_interface_orientations[slat.layer - 1][1], self.layer_interface_orientations[slat.layer][0]])
                handle_layers.extend([slat.layer - 2, slat.layer - 1])
                handle_plates.extend([crisscross_antihandle_plates,
                                      crisscross_handle_plates])  # handle orientation always assumed to follow same pattern

            for slat_position_index in range(slat.max_length):
                coords = slat.slat_position_to_coordinate[slat_position_index + 1]
                for layer, slat_side, sel_plates in zip(handle_layers, slat_crisscross_interfaces, handle_plates):
                    handle_val = handle_arrays[coords[0], coords[1], layer]
                    if handle_val < 1:  # no crisscross handles here
                        continue
                    self.slats[key].set_handle(slat_position_index + 1, slat_side,
                                               sel_plates.get_sequence(slat_position_index + 1, slat_side, handle_val),
                                               sel_plates.get_well(slat_position_index + 1, slat_side, handle_val),
                                               sel_plates.get_plate_name(slat_position_index + 1, slat_side,
                                                                         handle_val))

    def assign_seed_handles(self, seed_array, seed_plate, layer_id=1):
        """
        Assigns seed handles to the slats based on the seed array provided.
        :param seed_array: 2D array with positioning of seed.  Each row of the seed should have a unique ID.
        :param seed_plate: Plate class with sequences to draw from.
        """
        seed_coords = np.where(seed_array > 0)
        # TODO: more checks to ensure seed placement fits all parameters?
        for y, x in zip(seed_coords[0], seed_coords[1]):

            slat_ID = self.slat_array[y, x, layer_id-1]
            if slat_ID == 0:
                raise RuntimeError('There is a seed coordinate placed on a non-slat position.  '
                                   'Please re-verify your seed pattern array.')

            selected_slat = self.slats[self.get_slat_key(layer_id, slat_ID)]
            slat_position = selected_slat.slat_coordinate_to_position[(y, x)]
            seed_value = seed_array[y, x]

            if layer_id == 1:
                bottom_slat_side = self.layer_interface_orientations[0]
            else:
                bottom_slat_side = self.layer_interface_orientations[layer_id-1][1]

            if bottom_slat_side == 5:
                raise NotImplementedError('Seed placement on H5 side not yet supported.')

            if not isinstance(seed_plate.get_sequence(slat_position, 2, seed_value), str):
                raise RuntimeError('Seed plate selected cannot support placement on canvas.')

            selected_slat.set_handle(slat_position, bottom_slat_side,
                                     seed_plate.get_sequence(slat_position, 2, seed_value),
                                     seed_plate.get_well(slat_position, 2, seed_value),
                                     seed_plate.get_plate_name())

        if len(seed_coords[0]) == 0:
            print((Fore.RED + 'WARNING: No seed handles were set - is your seed pattern array correct?'))

    def assign_cargo_handles(self, cargo_array, cargo_plate, layer='top', requested_handle_orientation=None):
        """
        Assigns cargo handles to the megastructure slats based on the cargo array provided.
        :param cargo_array: 2D array containing cargo IDs (must match plate provided).
        :param cargo_plate: Plate class with sequences to draw from.
        :param layer: Either 'top' or 'bottom', or the exact layer ID required.
        :param requested_handle_orientation: If a middle layer is specified,
        then the handle orientation must be provided since there are always two options available.
        TODO: what to do if there are multiple cargo plates?
        TODO: what to do if there are string ids instead of float ids?
        """

        cargo_coords = np.where(cargo_array > 0)
        if layer == 'top':
            handle_orientation = self.layer_interface_orientations[-1]
            sel_layer = self.num_layers
            if requested_handle_orientation:
                raise RuntimeError('Handle orientation cannot be specified when '
                                   'placing cargo at the top of the design.')
        elif layer == 'bottom':
            handle_orientation = self.layer_interface_orientations[0]
            sel_layer = 1
            if requested_handle_orientation:
                raise RuntimeError('Handle orientation cannot be specified when '
                                   'placing cargo at the bottom of the design.')
        elif isinstance(layer, int):
            sel_layer = layer
            handle_orientation = requested_handle_orientation
        else:
            raise RuntimeError('Layer ID must be "top", "bottom" or an integer.')

        for y, x in zip(cargo_coords[0], cargo_coords[1]):
            slat_ID = self.slat_array[y, x, sel_layer-1]
            if slat_ID == 0:
                raise RuntimeError('There is a cargo coordinate placed on a non-slat position.  '
                                   'Please re-verify your cargo pattern array.')
            selected_slat = self.slats[self.get_slat_key(sel_layer, slat_ID)]
            slat_position = selected_slat.slat_coordinate_to_position[(y, x)]
            cargo_value = cargo_array[y, x]

            if not isinstance(cargo_plate.get_sequence(slat_position, handle_orientation, cargo_value), str):
                raise RuntimeError('Cargo plate selected cannot support placement on canvas.')

            selected_slat.set_handle(slat_position, handle_orientation,
                                     cargo_plate.get_sequence(slat_position, handle_orientation, cargo_value),
                                     cargo_plate.get_well(slat_position, handle_orientation, cargo_value),
                                     cargo_plate.get_plate_name())

    def patch_control_handles(self, control_plate):
        """
        Fills up all remaining holes in slats with no-handle control sequences.
        :param control_plate: Plate class with core sequences to draw from.
        """
        for key, slat in self.slats.items():
            for i in range(1, slat.max_length+1):
                if i not in slat.H2_handles:
                    slat.set_handle(i, 2,
                                    control_plate.get_sequence(i, 2, 0),
                                    control_plate.get_well(i, 2, 0),
                                    control_plate.get_plate_name())
                if i not in slat.H5_handles:
                    slat.set_handle(i, 5,
                                    control_plate.get_sequence(i, 5, 0),
                                    control_plate.get_well(i, 5, 0),
                                    control_plate.get_plate_name())

    def create_combined_graphical_view(self):
        """
        Creates combined arrays of all handles/cargo for plotting.
        TODO: This function is only good for the top/bottom layers - needs to be improved for a full all-layer view.
        :return:
        """
        # TODO: can consider adding cargo name to slat H2/H5 handles dict too for easy identication
        # TODO: reduce convolution here...
        plate_dict = {}
        bottom_layer = 'layer1'
        top_layer = f'layer{self.num_layers}'
        top_array = np.zeros_like(self.slat_array[:, :, 0])
        bottom_array = np.zeros_like(self.slat_array[:, :, 0])

        top_orientation = self.layer_interface_orientations[-1]
        bottom_orientation = self.layer_interface_orientations[0]

        for key, slat in self.slats.items():
            if bottom_layer in key:
                sel_orientation = bottom_orientation
                sel_array = bottom_array
            elif top_layer in key:
                sel_orientation = top_orientation
                sel_array = top_array
            else:
                continue
            for position, coord in slat.slat_position_to_coordinate.items():
                if sel_orientation == 2:
                    sel_plate = slat.H2_handles[position]['plate']
                else:
                    sel_plate = slat.H5_handles[position]['plate']
                if sel_plate not in plate_dict:
                    plate_dict[sel_plate] = len(plate_dict) + 1
                sel_array[coord[0], coord[1]] = plate_dict[sel_plate]

        return bottom_array, top_array
