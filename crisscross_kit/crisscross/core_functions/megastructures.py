import copy
from collections import defaultdict, OrderedDict
import numpy as np
import matplotlib.pyplot as plt
from colorama import Fore, Style
import os
import matplotlib as mpl
import pandas as pd
import platform
import ast

from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.slats import get_slat_key, convert_slat_array_into_slat_objects, Slat
from crisscross.helper_functions import create_dir_if_empty, natural_sort_key
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets
from crisscross.helper_functions.slat_salient_quantities import connection_angles
from crisscross.graphics.static_plots import create_graphical_slat_view, create_graphical_assembly_handle_view
from crisscross.graphics.pyvista_3d import create_graphical_3D_view
from crisscross.graphics.blender_3d import create_graphical_3D_view_bpy
from eqcorr2d.slat_standardized_mapping import generate_standardized_slat_handle_array
from eqcorr2d.eqcorr2d_interface import comprehensive_score_analysis

# consistent figure formatting between mac, windows and linux
if platform.system() == 'Darwin':
    plt.rcParams.update({'font.sans-serif': 'Helvetica'})
elif platform.system() == 'Windows':
    plt.rcParams.update({'font.sans-serif': 'Arial'})
else:
    plt.rcParams.update({'font.sans-serif': 'DejaVu Sans'}) # should work with linux


def next_capital_letter(current: str) -> str:
    chars = [ord(c) - ord('A') for c in current]
    for i in range(len(chars) - 1, -1, -1):
        if chars[i] < 25:
            chars[i] += 1
            return ''.join(chr(ord('A') + c) for c in chars)
        else:
            chars[i] = 0
    # All were 'Z', prepend 'A'
    return 'A' + ''.join(chr(ord('A') + c) for c in chars)

def create_default_layer_palette(layer_interface_orientations):
    layer_palette = {}
    cmap = mpl.colormaps['Dark2']
    dark2_colors = [mpl.colors.to_hex(cmap(i)) for i in range(cmap.N)]
    layer_id = 'A'
    for i, orientation in enumerate(layer_interface_orientations[:-1]):
        layer_palette[i + 1] = {'color': dark2_colors[i % len(dark2_colors)], 'ID': layer_id}
        if i == 0:
            layer_palette[i + 1]['bottom'] = orientation
            layer_palette[i + 1]['top'] = layer_interface_orientations[i + 1][0]
        elif i == len(layer_interface_orientations) - 2:
            layer_palette[i + 1]['bottom'] = orientation[1]
            layer_palette[i + 1]['top'] = layer_interface_orientations[i + 1]
        else:
            layer_palette[i + 1]['bottom'] = orientation[1]
            layer_palette[i + 1]['top'] = layer_interface_orientations[i + 1][0]
        layer_id = next_capital_letter(layer_id)
    return layer_palette

def export_layer_orientations_to_list_format(layer_palette):
    num_layers = len(layer_palette)
    layer_interface_orientations = []

    # First orientation is just the bottom of the first layer
    first_layer = layer_palette[1]
    layer_interface_orientations.append(first_layer['bottom'])

    for i in range(1, num_layers+1):
        layer = layer_palette[i]
        next_layer = layer_palette[i + 1] if i + 1 in layer_palette else None

        if next_layer is not None:
            layer_interface_orientations.append((layer['top'], next_layer['bottom']))
        else:
            layer_interface_orientations.append(layer['top'])  # final top

    return layer_interface_orientations


class Megastructure:
    """
    Convenience class that bundles the entire details of a megastructure including slat positions, seed handles and cargo.
    """

    def __init__(self, slat_array=None, layer_interface_orientations=None, connection_angle='90', import_design_file=None):
        """
        :param slat_array: Array of slat positions (3D - X,Y, layer ID) containing the positions of all slats in the design.
        :param layer_interface_orientations: The direction each slat will be facing in the design.
        :param connection_angle: The angle at which the slats will be connected.  For now, only 90 and 60 grids are supported.
        E.g. for a 2 layer design, [2, 5, 2] implies that the bottom layer will have H2 handles sticking out,
        the connecting interface will have H5 handles and the top layer will have H2 handles again.
        TODO: how do we consider the additional 12nm/6nm on either end of the slat?
        """

        # reads in all design details from file if available
        if import_design_file is not None:
            slats, handle_arrays, seed_dict, cargo_dict, connection_angle, layer_palette, cargo_palette, hashcad_canvas_metadata, slat_grid_coords = self.import_design(import_design_file)
            self.layer_palette = layer_palette
            self.cargo_palette = cargo_palette
            self.hashcad_canvas_metadata = hashcad_canvas_metadata
            self.slats = slats
            self.slat_grid_coords = slat_grid_coords
            self.original_slat_array = self.generate_slat_occupancy_grid()
        else:
            if slat_array is None:
                raise RuntimeError('A slat array must be provided to initialize the megastructure (either imported or directly).')
            handle_arrays = None
            seed_dict = None
            cargo_dict = {}
            self.cargo_palette = {}
            self.hashcad_canvas_metadata = {'canvas_offset_min': (0.0, 0.0), 'canvas_offset_max':(0.0, 0.0)}
            num_layers = slat_array.shape[2]
            self.slats = convert_slat_array_into_slat_objects(slat_array)
            self.slat_grid_coords = (slat_array.shape[0], slat_array.shape[1])

            # if no custom interface supplied, assuming alternating H2/H5 handles,
            # with H2 at the bottom, H5 at the top, and alternating connections in between
            # e.g. for a 3-layer structure, layer_interface_orientations = [2, (5, 2), (5,2), 5]
            if layer_interface_orientations is None:
                layer_interface_orientations = [2] + [(5, 2)] * (num_layers - 1) + [5]

            self.layer_palette = create_default_layer_palette(layer_interface_orientations)
            self.original_slat_array = slat_array

        if connection_angle not in ['60', '90']:
            raise NotImplementedError('Only 90 and 60 degree connection angles are supported.')

        # these are the grid distance jump per point, which are different for the two connection angles
        self.connection_angle = connection_angle
        self.grid_xd = connection_angles[connection_angle][0]
        self.grid_yd = connection_angles[connection_angle][1]

        # if design file was provided, the seed, handles and cargo can be pre-assigned here
        if seed_dict is not None:
            self.assign_seed_handles(seed_dict)
        if handle_arrays is not None:
            self.assign_assembly_handles(handle_arrays)
        if len(cargo_dict) > 0:
            self.assign_cargo_handles_with_dict(cargo_dict)


    def assign_colormap_for_cargo(self, colormap='Dark2'):
        color_list = mpl.colormaps[colormap].colors
        for ind, cargo_key in enumerate(self.cargo_palette.keys()):
            self.cargo_palette[cargo_key]['color'] = color_list[ind % len(color_list)]

    def assign_colormap_for_slats(self, colormap='Set1'):
        color_list = mpl.colormaps[colormap].colors
        for l in range(len(self.layer_palette)):
            self.layer_palette[l + 1]['color'] = color_list[l % len(color_list)]

    def assign_handle_to_slat(self, slat, slat_position_index, slat_side, handle_val, category, descriptor, sel_plates, update=False):
        if sel_plates is None:
            slat.set_placeholder_handle(slat_position_index, slat_side, category, handle_val, descriptor='Placeholder|%s' % descriptor)
        else:
            sequence = sel_plates.get_sequence(category, slat_position_index, slat_side, handle_val)
            well = sel_plates.get_well(category, slat_position_index, slat_side, handle_val)
            plate_name = sel_plates.get_plate_name(category, slat_position_index, slat_side, handle_val)
            concentration = sel_plates.get_concentration(category, slat_position_index, slat_side, handle_val)

            if update:
                slat.update_placeholder_handle(slat_position_index, slat_side, sequence, well, plate_name,
                                category, handle_val, concentration, descriptor=descriptor)
            else:
                slat.set_handle(slat_position_index, slat_side, sequence, well, plate_name,
                                category, handle_val, concentration, descriptor=descriptor)

    def assign_assembly_handles(self, handle_arrays, crisscross_handle_plates=None, crisscross_antihandle_plates=None):
        """
        Assigns crisscross handles to the slats based on the handle arrays provided.
        :param handle_arrays: 3D array of handle values (X, Y, layer) where each value corresponds to a handle ID.
        :param crisscross_handle_plates: Crisscross handle plates.  If not supplied, a placeholder will be added to the slat instead.
        :param crisscross_antihandle_plates: Crisscross anti-handle plates.  If not supplied, a placeholder will be added to the slat instead.
        TODO: this function assumes the pattern is always handle -> antihandle -> handle -> antihandle etc. Can we make this customizable?
        :return: N/A
        """

        if handle_arrays.shape[2] != len(self.layer_palette) - 1:
            raise RuntimeError('Need to specify the correct number of layers when assigning crisscross handles.')

        for key, slat in self.slats.items():
            sides = []
            if slat.layer == 1:
                sides.append('top')
            elif slat.layer == len(self.layer_palette):
                sides.append('bottom')
            else:
                sides.extend(['top', 'bottom'])

            for slat_position_index in range(slat.max_length):
                coords = slat.slat_position_to_coordinate[slat_position_index + 1]
                for side in sides:
                    slat_side = self.layer_palette[slat.layer][side]
                    if side == 'top':
                        handle_val = int(handle_arrays[coords[0], coords[1], slat.layer-1])
                        sel_plates = crisscross_handle_plates
                        category = 'HANDLE'
                    else:
                        handle_val = int(handle_arrays[coords[0], coords[1], slat.layer-2])
                        sel_plates = crisscross_antihandle_plates
                        category = 'ANTIHANDLE'
                    if handle_val > 0:
                        self.assign_handle_to_slat(slat, slat_position_index + 1, slat_side, str(handle_val), 'ASSEMBLY_%s' % category, 'Assembly|%s|%s' % (category.capitalize(), handle_val), sel_plates)

    def assign_seed_handles(self, seed_dict, seed_plate=None):
        """
        Assigns seed handles to the slats based on the seed dictionary provided.
        """

        slat_occupancy_grid = self.generate_slat_occupancy_grid()

        for (seed_id, layer, side), seed_data in seed_dict.items():
            for (y, x, handle_id) in seed_data:
                    slat_ID = slat_occupancy_grid[y, x, layer-1]
                    if slat_ID == 0:
                        raise RuntimeError('There is a seed coordinate placed on a non-slat position.  '
                                           'Please re-verify your seed pattern array.')

                    selected_slat = self.slats[get_slat_key(layer, slat_ID)]

                    slat_position = selected_slat.slat_coordinate_to_position[(y, x)]

                    if seed_plate is not None:
                        if not isinstance(seed_plate.get_sequence(slat_position, side, handle_id), str):
                            raise RuntimeError('Seed plate selected cannot support placement on canvas.')

                    self.assign_handle_to_slat(selected_slat, slat_position, side, handle_id, 'SEED', 'Seed|%s|%s' % (handle_id, seed_id), seed_plate)

    def generate_slat_occupancy_grid(self, use_original_slat_array=False):
        """
        Generates a 3D occupancy grid of the slats in the design.
        :return: 3D numpy array with slat IDs at each position (X, Y, layer)
        """

        if use_original_slat_array:
            return self.original_slat_array

        occupancy_grid = np.zeros((self.slat_grid_coords[0], self.slat_grid_coords[1], len(self.layer_palette)), dtype=int)

        for key, slat in self.slats.items():
            if not slat.non_assembly_slat:
                for y, x in slat.slat_coordinate_to_position.keys():
                    occupancy_grid[y, x, slat.layer - 1] = int(slat.ID.split('slat')[-1])

        return occupancy_grid

    def generate_assembly_handle_grid(self):
        """
        Generates a 3D occupancy grid of the assembly handles in the design.
        :return: 3D numpy array with handle IDs at each position (X, Y, layer)
        """

        handle_grid = np.zeros((self.slat_grid_coords[0], self.slat_grid_coords[1], len(self.layer_palette)-1), dtype=int)

        for key, slat in self.slats.items():
            for side in [2, 5]:
                for handle_position, handle_data in slat.get_sorted_handles('h%s' % side):
                    if 'ASSEMBLY' in handle_data['category']:
                        y, x = slat.slat_position_to_coordinate[handle_position]
                        if self.layer_palette[slat.layer]['top'] == side:
                            handle_layer = slat.layer - 1
                        else:
                            handle_layer = slat.layer - 2
                        if handle_grid[y, x, handle_layer] != 0 and handle_grid[y, x, handle_layer] != int(handle_data['value']):
                            raise RuntimeError('There is a handle conflict at position (%d, %d) on assembly handle layer %d. '
                                               'Handle %s conflicts with existing handle %s.' %
                                               (y, x, handle_layer, handle_data['value'], handle_grid[y, x, handle_layer]))

                        handle_grid[y, x, handle_layer] = int(handle_data['value'])

        return handle_grid

    def generate_seed_coordinates(self):

        seed_coordinate_dict = defaultdict(list)
        for key, slat in self.slats.items():
            for side in [2, 5]:
                for handle_position, handle_data in slat.get_sorted_handles('h%s' % side):
                    if 'SEED' in handle_data['category']:
                        y, x = slat.slat_position_to_coordinate[handle_position]
                        seed_coordinate_dict[(slat.layer, handle_data['descriptor'].split('|')[-1])].append((y, x))

        return seed_coordinate_dict

    def generate_cargo_coordinates(self):

        cargo_coodinate_dict = defaultdict(list)
        for key, slat in self.slats.items():
            for side in [2, 5]:
                for handle_position, handle_data in slat.get_sorted_handles('h%s' % side):
                    if 'CARGO' in handle_data['category']:
                        y, x = slat.slat_position_to_coordinate[handle_position]
                        cargo_coodinate_dict[(slat.layer, side, handle_data['value'])].append((y, x))

        return cargo_coodinate_dict

    def assign_cargo_handles_with_dict(self, cargo_dict, cargo_plate=None):
        """
        Assigns cargo handles to the megastructure slats based on the cargo dictionary provided.
        :param cargo_dict: Dictionary of cargo placements (key = slat position, layer, handle orientation, value = cargo ID)
        :param cargo_plate: The cargo plate from which cargo will be assigned.  If not provided, a placeholder will be assigned instead.
        :return: N/A
        """

        slat_occupancy_grid = self.generate_slat_occupancy_grid()
        default_colors = mpl.colormaps['Dark2'].colors
        next_color = 0

        for key, cargo_value in cargo_dict.items():
            y_pos = key[0][0]
            x_pos = key[0][1]
            layer = key[1]
            handle_orientation = key[2]
            slat_ID = slat_occupancy_grid[y_pos, x_pos, layer - 1]

            if '-' in cargo_value:
                cargo_value = cargo_value.replace('-', '_')
                print(Fore.YELLOW + f'WARNING: Cargo value {cargo_value} contains a -, which is unsupported. It has been changed to an _.')

            if slat_ID == 0:
                raise RuntimeError('There is a cargo coordinate placed on a non-slat position.  '
                                   'Please re-verify your cargo pattern array.')

            selected_slat = self.slats[get_slat_key(layer, slat_ID)]
            slat_position = selected_slat.slat_coordinate_to_position[(y_pos, x_pos)]

            if cargo_plate is not None:
                if not isinstance(cargo_plate.get_sequence('CARGO', slat_position, handle_orientation, cargo_value), str):
                    raise RuntimeError('Cargo plate selected cannot support placement on canvas.')

            if cargo_value not in self.cargo_palette:
                self.cargo_palette[cargo_value] = {'short name': cargo_value[0:2].upper(), 'color': default_colors[next_color]}
                next_color = (next_color + 1) % len(default_colors)

            self.assign_handle_to_slat(selected_slat, slat_position, handle_orientation, cargo_value, 'CARGO', 'Cargo|%s' % cargo_value, cargo_plate)

    def convert_cargo_array_into_cargo_dict(self, cargo_array, cargo_keymap, layer, handle_orientation=None):
        """
        Converts a cargo array into a dictionary that can be used to assign cargo handles to the slats.
        :param cargo_array: Numpy array with cargo IDs (and 0s where no cargo is present).
        :param cargo_keymap: A dictionary converting cargo ID numbers into unique strings.
        :param layer: The layer the cargo should be assigned to (either top, bottom or a specific number)
        :param handle_orientation: The specific slat handle orientation to which the cargo is assigned.
        :return: Dictionary of converted cargo.
        """

        cargo_coords = np.where(cargo_array > 0)
        cargo_dict = {}
        if layer == 'top':
            layer = len(self.layer_palette)
            if handle_orientation:
                raise RuntimeError('Handle orientation cannot be specified when '
                                   'placing cargo at the top of the design.')
            handle_orientation = self.layer_palette[layer]['top']

        elif layer == 'bottom':
            layer = 1
            if handle_orientation:
                raise RuntimeError('Handle orientation cannot be specified when '
                                   'placing cargo at the top of the design.')
            handle_orientation = self.layer_palette[1]['bottom']
        elif handle_orientation is None:
            raise RuntimeError('Handle orientation must specified when '
                               'placing cargo on middle layers of the design.')

        for y, x in zip(cargo_coords[0], cargo_coords[1]):
            cargo_value = cargo_keymap[cargo_array[y, x]]
            cargo_dict[((y, x), layer, handle_orientation)] = cargo_value

        return cargo_dict

    def assign_cargo_handles_with_array(self, cargo_array, cargo_key, cargo_plate=None, layer='top',
                                        handle_orientation=None):
        """
        Assigns cargo handles to the megastructure slats based on the cargo array provided.
        :param cargo_array: 2D array containing cargo IDs (must match plate provided).
        :param cargo_key: Dictionary mapping cargo IDs to cargo unique names for proper identification.
        :param cargo_plate: Plate class with sequences to draw from.  If not provided, a placeholder will be assigned instead.
        :param layer: Either 'top' or 'bottom', or the exact layer ID required.
        :param handle_orientation: If a middle layer is specified,
        then the handle orientation must be provided since there are always two options available.
        """
        cargo_dict = self.convert_cargo_array_into_cargo_dict(cargo_array, cargo_key, layer=layer,
                                                              handle_orientation=handle_orientation)
        self.assign_cargo_handles_with_dict(cargo_dict, cargo_plate)

    def patch_placeholder_handles(self, plates):
        """
        Patches placeholder handles with actual handles based on the plates provided.
        :param plates: List of plates from which to extract handles.
        :return: N/A
        """
        for key, slat in self.slats.items():
            placeholder_list = copy.copy(slat.placeholder_list)
            for placeholder_handle in placeholder_list:  # runs through all placeholders on current slat
                handle_position = int(placeholder_handle.split('|')[1])  # extracts handle, orientation and cargo ID from placeholder
                orientation = int(placeholder_handle.split('|')[-1][1:])

                if orientation == 2:
                    handle_data = slat.H2_handles[handle_position]
                else:
                    handle_data = slat.H5_handles[handle_position]

                plate_key = (handle_data['category'], handle_position, orientation, handle_data['value'])

                for plate in plates:
                    if not isinstance(plate.get_sequence(*plate_key), bool):
                        self.assign_handle_to_slat(slat, handle_position, orientation, handle_data['value'],
                                                   handle_data['category'],
                                                   handle_data['descriptor'].split('Placeholder|')[-1], plate, update=True)
                        break

            if len(slat.placeholder_list) > 0:
                print(Fore.RED + f'WARNING: Placeholder handles on slat {key} still remain after patching.')
                for handle in slat.placeholder_list:
                    position, side = handle.split('|')[1:]
                    if side == 'h2':
                        category = slat.H2_handles[int(position)]['category']
                    else:
                        category = slat.H5_handles[int(position)]['category']
                    if category == 'SEED':
                        print(Fore.RED + f'WARNING: Seems like you are missing a seed handle - could your seed be flipped by mistake?')
                        break

    def patch_flat_staples(self, flat_plate):
        """
        Fills up all remaining holes in slats with no-handle control sequences.
        :param flat_plate: Plate class with flat sequences to draw from.
        """
        for key, slat in self.slats.items():
            for i in range(1, slat.max_length + 1):
                if i not in slat.H2_handles:
                    self.assign_handle_to_slat(slat, i, 2, 'BLANK', 'FLAT', 'Flat', flat_plate)
                if i not in slat.H5_handles:
                    self.assign_handle_to_slat(slat, i, 5, 'BLANK', 'FLAT', 'Flat', flat_plate)

    def get_slats_by_assembly_stage(self, minimum_handle_cutoff=16):
        """
        Runs through the design and separates out all slats into groups sorted on their predicted assembly stage.
        :param minimum_handle_cutoff: Minimum number of handles that need to be present for a slat to be considered stably setup.
        :return: Dict of slats (key = slat ID, value = assembly order)
        """

        slat_count = 0
        slat_groups = []
        complete_slats = set()
        special_slats = []
        rational_slat_count = len(self.slats)
        slat_array = self.generate_slat_occupancy_grid()
        seed_coordinates_dict = self.generate_seed_coordinates()
        if len(seed_coordinates_dict) == 0:
            raise RuntimeError('No seed coordinates found in the design - slat animation cannot be predicted without a seed.')

        for s_key, s_val in self.slats.items():
            if s_val.layer < 1 or s_val.layer > len(self.layer_palette) or s_val.non_assembly_slat:  # these slats can never be rationally identified, and should be animated in last
                special_slats.append(s_val.ID)
                rational_slat_count -= 1

        # TODO: this probably won't work well when there are multiple seeds...
        while slat_count < rational_slat_count:  # will loop through the design until all slats have been given a home
            if slat_count == 0:  # first extracts slats that will attach to the seed
                first_step_slats = set()
                for (seed_layer, seed_key), seed_coords in seed_coordinates_dict.items():
                    for (y, x) in seed_coords:  # extracts the slat ids from the layer connecting to the seed
                        overlapping_slat = (seed_layer, slat_array[y, x,seed_layer - 1])
                        first_step_slats.add(overlapping_slat)

                complete_slats.update(first_step_slats)  # tracks all slats that have been assigned a group
                slat_count += len(first_step_slats)
                slat_groups.append(list(first_step_slats))

            else:
                slat_overlap_counts = defaultdict(int)
                # these loops will check all slats in all groups to see if a combination
                # of different slats provide enough of a foundation for a new slat to attach
                for slat_group in slat_groups:
                    for layer, slat in slat_group:
                        slat_posns = np.where(slat_array[..., layer - 1] == slat)
                        for y, x in zip(slat_posns[0], slat_posns[1]):
                            if layer != 1 and slat_array[y, x, layer - 2] != 0:  # checks the layer below
                                slat_overlap_counts[(layer - 1, slat_array[y, x, layer - 2])] += 1
                            if layer != len(self.layer_palette) and slat_array[y, x, layer] != 0:  # checks the layer above
                                slat_overlap_counts[(layer + 1, slat_array[y, x, layer])] += 1
                next_slat_group = []
                for k, v in slat_overlap_counts.items():
                    # a slat is considered stable when it has the defined minimum handle count stably attached
                    if v >= minimum_handle_cutoff and k not in complete_slats:
                        next_slat_group.append(k)
                complete_slats.update(next_slat_group)
                slat_groups.append(next_slat_group)
                slat_count += len(next_slat_group)


        slat_id_animation_classification = {}

        # final loop to further separate all slats in a group into several sub-groups based on their layer.
        # This should match reality more but then the issue is that it is impossible to predict which group will
        # be assembled first (this depends on what the user prefers).
        # In that case, the user will need to supply their own manual slat groups.
        group_tracker = 0
        for _, group in enumerate(slat_groups):
            current_layer = 0
            for slat in group:
                if current_layer == 0:
                    current_layer = slat[0]
                elif current_layer != slat[0]:
                    group_tracker += 1
                    current_layer = slat[0]
                slat_id_animation_classification[get_slat_key(*slat)] = group_tracker
            group_tracker += 1

        for s_slat in special_slats:  # adds special slats at the end
            slat_id_animation_classification[s_slat] = group_tracker

        return slat_id_animation_classification

    def get_slat_match_counts(self, use_original_slat_array=False, use_external_handle_array=None):
        """
        Runs through the design and counts how many slats have a certain number of connections (matches) to other slats.
        Useful for computing the hamming distance of a design with variable slat types.
        :return: Dictionary of match counts (key = number of matches, value = number of slat pairs with that many matches),
         and a connection graph that lists all slat pairs with a certain number of matches.
        TODO: what to do in the case of slats with multiple layers e.g. the sierpinski slats?
        """

        megastructure_match_count = defaultdict(int) # key = number of matches, value = number of slat pairs with that many matches
        completed_slats = set() # just a tracker to prevent duplicate entries
        connection_graph = defaultdict(list)

        # arrays obtained from design as usual
        slat_array = self.generate_slat_occupancy_grid(use_original_slat_array=use_original_slat_array)
        if use_external_handle_array:
            handle_array = use_external_handle_array
        else:
            handle_array = self.generate_assembly_handle_grid()

        # loops through all slats in the design
        for s_key, slat in self.slats.items():
            if not slat.non_assembly_slat:
                matches_with_other_slats = defaultdict(int)

                # checks slats in the layer above
                if slat.layer != slat_array.shape[-1]:
                    # runs through all the coordinates of a specific slat
                    for coordinate in slat.slat_position_to_coordinate.values():

                        # checks if there's a handle match
                        if handle_array[coordinate[0], coordinate[1], slat.layer-1] != 0:

                            other_slat = slat_array[coordinate[0], coordinate[1], slat.layer]
                            # ignores areas where there are actually no overlapping slats
                            if other_slat == 0:
                                continue

                            # records match
                            other_slat_key = get_slat_key(slat.layer+1, other_slat)
                            if other_slat_key not in completed_slats:
                                matches_with_other_slats[other_slat_key] += 1

                # checks slats in the layer below - same logic as above
                if slat.layer != 1:
                    for coordinate in slat.slat_position_to_coordinate.values():
                        if handle_array[coordinate[0], coordinate[1], slat.layer - 2] != 0:
                            other_slat = slat_array[coordinate[0], coordinate[1], slat.layer - 2]
                            if other_slat == 0:
                                continue
                            other_slat_key = get_slat_key(slat.layer - 1, other_slat)
                            if other_slat_key not in completed_slats:
                                matches_with_other_slats[other_slat_key] += 1

                # enumerates all matches found and updates the overall count
                for k, v in matches_with_other_slats.items():
                    megastructure_match_count[v] += 1
                    connection_graph[v].append((s_key, k))

                # prevents other slats from matching with this slat again
                completed_slats.add(s_key)

        return megastructure_match_count, connection_graph

    def get_bag_of_slat_handles(self, use_original_slat_array=False, use_external_handle_array=None, remove_blank_slats=False):
        """
        Obtains two dictionaries - both containing the arrays corresponding to the handle positions of each slat in the
        megastructure (one for handles and one for antihandles).  The keys correspond to the slat ID while the values contain
        individual numpy handle arrays, one for each slat.  The handle arrays represent the actual 2D shape of the slat
        in the design.  Non-2D 60 degree slats are converted into 2D triangular coordinates to make handle match computation
        significantly simpler.
        """
        handle_dict = OrderedDict()
        antihandle_dict = OrderedDict()

        # arrays obtained from design as usual
        slat_array = self.generate_slat_occupancy_grid(use_original_slat_array=use_original_slat_array)
        if use_external_handle_array is None:
            handle_array = self.generate_assembly_handle_grid()
        else:
            handle_array = use_external_handle_array

        # loops through all slats in the design
        for s_key, slat in self.slats.items():
            if not slat.non_assembly_slat:
                rows, cols = zip(*list(slat.slat_position_to_coordinate.values()))
                # STANDARD TUBULAR SLATS CAN BE CONVERTED INTO 1D ARRAYS DIRECTLY
                # checks slats in the layer above
                if slat.layer != slat_array.shape[-1]:
                    handle_dict[s_key] = handle_array[rows, cols, slat.layer-1]

                # checks slats in the layer below - same logic as above
                if slat.layer != 1:
                    antihandle_dict[s_key] = handle_array[rows, cols, slat.layer-2]

                # DB Slats in 60deg mode need to be converted into their standard 90deg format
                if slat.slat_type != 'tube':
                    if self.connection_angle == '60':
                        if s_key in handle_dict:
                            handle_dict[s_key] = generate_standardized_slat_handle_array(handle_dict[s_key], slat.slat_type)
                        if s_key in antihandle_dict:
                            antihandle_dict[s_key] = generate_standardized_slat_handle_array(antihandle_dict[s_key], slat.slat_type)
                    else:
                        # extract the exact shape from the handle array
                        min_row, max_row = min(rows), max(rows)
                        min_col, max_col = min(cols), max(cols)
                        if s_key in handle_dict:
                            sub_array = handle_array[min_row:max_row + 1, min_col:max_col + 1, slat.layer-1]
                            handle_dict[s_key] = sub_array
                        if s_key in antihandle_dict:
                            sub_array = handle_array[min_row:max_row + 1, min_col:max_col + 1, slat.layer-2]
                            antihandle_dict[s_key] = sub_array

        if remove_blank_slats:
            # remove all numpy arrays with all zeros (i.e. no handles/antihandles)
            handle_dict = {k: v for k, v in handle_dict.items() if np.sum(v) > 0}
            antihandle_dict = {k: v for k, v in antihandle_dict.items() if np.sum(v) > 0}

        return handle_dict, antihandle_dict

    def get_match_strength_score(self):
        """
        Computes the match strength score of the megastructure design based on the assembly handles present.
        4 items are provided in a dictionary:
        - the worst match score (i.e. the maximum number of matches between any two slats in the design)
        - the mean log score (i.e. the log of the mean number of matches between all slat pairs in the design)
        - the similarity score (i.e. the maximum number of matches between slats of the same type, which could result
        in a slat taking the place of another slat in the design if strong enough)
        - the full match histogram, which could be helpful for investigating designs with unexpected scores.
        """
        # TODO: this function also assumes the pattern handle -> antihandle -> handle -> antihandle etc.
        # TODO: the below two functions both request the slat/handle arrays individually, is this a problem?

        # first extract all handles/antihandles in the design
        handle_dict, antihandle_dict = self.get_bag_of_slat_handles(remove_blank_slats=True)

        # gets the number of matches that are expected in the design based on slat overlaps,
        # these will be removed from the final histogram
        match_counts, connection_graph = self.get_slat_match_counts()

        return comprehensive_score_analysis(handle_dict, antihandle_dict, match_counts, connection_graph, self.connection_angle)


    def create_graphical_slat_view(self, save_to_folder=None, instant_view=True,
                                   include_cargo=True, include_seed=True,
                                   filename_prepend='',
                                   colormap=None, cargo_colormap=None):
        """
        Creates a graphical view of the slats, cargo and seeds in the design.  Refer to the graphics module for more details.
        :param save_to_folder: Set to the filepath of a folder where all figures will be saved.
        :param instant_view: Set to True to plot the figures immediately to your active view.
        :param include_cargo: Set to True to include cargo in the graphical view.
        :param include_seed: Set to True to include the seed in the graphical view.
        :param filename_prepend: String to prepend to the filename of generated figures.
        :param colormap: The colormap to sample from for each additional layer.
        :param cargo_colormap: The colormap to sample from for each cargo type.
        :return: N/A
        """
        slat_array = self.generate_slat_occupancy_grid()
        if cargo_colormap is not None:
            self.assign_colormap_for_cargo(cargo_colormap)
        if colormap is not None:
            self.assign_colormap_for_slats(colormap)

        create_graphical_slat_view(slat_array,
                                   layer_palette=self.layer_palette,
                                   cargo_palette=self.cargo_palette,
                                   slats=self.slats,
                                   save_to_folder=save_to_folder, instant_view=instant_view,
                                   connection_angle=self.connection_angle,
                                   include_cargo=include_cargo,
                                   filename_prepend=filename_prepend,
                                   include_seed=include_seed)

    def create_graphical_assembly_handle_view(self, save_to_folder=None, instant_view=True, filename_prepend='', colormap=None):
        """
        Creates a graphical view of the assembly handles in the design.  Refer to the graphics module for more details.
        :param save_to_folder: Set to the filepath of a folder where all figures will be saved.
        :param instant_view: Set to True to plot the figures immediately to your active view.
        :param filename_prepend: String to prepend to the filename of generated figures.
        :param colormap: The colormap to sample from for each additional layer.
        :return: N/A
        """

        slat_array = self.generate_slat_occupancy_grid()
        handle_array = self.generate_assembly_handle_grid()

        if np.sum(handle_array) == 0:
            print(Fore.RED + 'No handle graphics will be generated as no handle arrays have been assigned to the design.' + Fore.RESET)
            return

        if colormap is not None:
            self.assign_colormap_for_slats(colormap)

        create_graphical_assembly_handle_view(slat_array, handle_array,
                                              layer_palette=self.layer_palette,
                                              filename_prepend=filename_prepend,
                                              slats=self.slats, save_to_folder=save_to_folder,
                                              connection_angle=self.connection_angle,
                                              instant_view=instant_view)

    def create_graphical_3D_view(self, save_folder, window_size=(2048, 2048), filename_prepend='', colormap=None, cargo_colormap=None):
        """
        Creates a 3D video of the megastructure slat design.
        :param save_folder: Folder to save all video to.
        :param window_size: Resolution of video generated.  2048x2048 seems reasonable in most cases.
        :param filename_prepend: String to prepend to the filename of the video.
        :param colormap: Colormap to extract layer colors from
        :param cargo_colormap: Colormap to extract cargo colors from
        :return: N/A
        """

        slat_array = self.generate_slat_occupancy_grid()
        if cargo_colormap is not None:
            self.assign_colormap_for_cargo(cargo_colormap)
        if colormap is not None:
            self.assign_colormap_for_slats(colormap)

        create_graphical_3D_view(slat_array, save_folder=save_folder, slats=self.slats, connection_angle=self.connection_angle,
                                 layer_palette=self.layer_palette, cargo_palette=self.cargo_palette,filename_prepend=filename_prepend,
                                 window_size=window_size)

    def create_blender_3D_view(self, save_folder, animate_assembly=False, animation_type='translate',
                               custom_assembly_groups=None, slat_translate_dict=None, minimum_slat_cutoff=15,
                               camera_spin=False, correct_slat_entrance_direction=True, force_slat_color_by_layer=True,
                               colormap=None, cargo_colormap=None, slat_flip_list=None, include_bottom_light=False,
                               filename_prepend=''):
        """
        Creates a 3D model of the megastructure slat design as a Blender file.
        :param save_folder: Folder to save all video to.
        :param animate_assembly: Set to true to also generate an animation of the design being assembled group by group.
        :param animation_type: Type of animation to generate.  Options are 'translate' and 'wipe_in'.
        :param custom_assembly_groups: If set, will use the specific provided dictionary to assign slats to the animation order.
        :param slat_translate_dict: If set, will use the specific provided dictionary to assign specific
        animation translation distances to each slat.
        :param minimum_slat_cutoff: Minimum number of slats that need to be present for a slat to be considered stable.
        You might want to vary this number as certain designs have staggers that don't allow for a perfect 16-slat binding system.
        :param camera_spin: Set to true to have camera spin around object during the animation.
        :param correct_slat_entrance_direction: If set to true, will attempt to correct the slat entrance animation to
        always start from a place that is supported.
        :param force_slat_color_by_layer: If set to true, will force the slat color to be the same as the layer color, regardless of the animation groups.
        :param colormap: Colormap to extract layer colors from
        :param cargo_colormap: Colormap to extract cargo colors from
        :param slat_flip_list: List of slat IDs - if a slat is in this list, its animation direction will be flipped.
        This cannot be used in conjunction with the correct_slat_entrance_direction parameter.
        :param include_bottom_light: Set to true to add a light source at the bottom of the design.
        :param filename_prepend: String to prepend to the filename of the Blender file.
        :return: N/A
        """
        if animate_assembly:
            if custom_assembly_groups:
                assembly_groups = custom_assembly_groups
            else:
                assembly_groups = self.get_slats_by_assembly_stage(minimum_handle_cutoff=minimum_slat_cutoff)
        else:
            assembly_groups = None

        slat_array = self.generate_slat_occupancy_grid()
        if cargo_colormap is not None:
            self.assign_colormap_for_cargo(cargo_colormap)
        if colormap is not None:
            self.assign_colormap_for_slats(colormap)

        create_graphical_3D_view_bpy(slat_array, slats=self.slats,
                                     save_folder=save_folder,
                                     layer_palette=self.layer_palette,
                                     cargo_palette=self.cargo_palette,
                                     animate_slat_group_dict=assembly_groups,
                                     connection_angle=self.connection_angle,
                                     animation_type=animation_type, camera_spin=camera_spin,
                                     correct_slat_entrance_direction=correct_slat_entrance_direction,
                                     slat_flip_list=slat_flip_list,
                                     force_slat_color_by_layer=force_slat_color_by_layer,
                                     specific_slat_translate_distances=slat_translate_dict,
                                     include_bottom_light=include_bottom_light,
                                     filename_prepend=filename_prepend)

    def create_standard_graphical_report(self, output_folder,
                                         generate_3d_video=True,
                                         colormap=None, cargo_colormap=None, filename_prepend=''):
        """
        Generates entire set of graphical reports for the megastructure design.
        :param output_folder: Output folder to save all images to.
        :param generate_3d_video: If set to true, will generate a 3D video of the design.
        :param colormap: Colormap to extract layer colors from.
        :param cargo_colormap: Colormap to extract cargo colors from.
        :param filename_prepend: String to prepend to the filename of generated figures.
        :return: N/A
        """
        print(Fore.CYAN + 'Generating graphical reports for megastructure design, this might take a few seconds...')
        create_dir_if_empty(output_folder)
        self.create_graphical_slat_view(save_to_folder=output_folder, instant_view=False, colormap=colormap, cargo_colormap=cargo_colormap, filename_prepend=filename_prepend)
        self.create_graphical_assembly_handle_view(save_to_folder=output_folder, instant_view=False, colormap=colormap, filename_prepend=filename_prepend)
        if generate_3d_video:
            self.create_graphical_3D_view(save_folder=output_folder, colormap=colormap, cargo_colormap=cargo_colormap, filename_prepend=filename_prepend)

        print(Style.RESET_ALL)

    def export_design(self, filename, folder):
        """
        Exports the entire design to a single excel file.
        All individual slat, cargo, handle and seed arrays are exported into separate sheets.
        :param filename: Output .xlsx filename
        :param folder: Output folder
        :return: N/A
        """

        def write_array_to_excel(writer, array, sheet_prefix):
            for layer_index in range(array.shape[-1]):
                df = pd.DataFrame(array[..., layer_index])
                sheet_name = f'{sheet_prefix}_{layer_index + 1}'
                df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                writer.sheets[sheet_name].conditional_format( 0, 0, df.shape[0], df.shape[1] - 1, excel_conditional_formatting)

        writer = pd.ExcelWriter(os.path.join(folder, filename), engine='xlsxwriter')
        workbook = writer.book
        excel_conditional_formatting = {'type': '3_color_scale',
                                        'criteria': '<>',
                                        'min_color': "#63BE7B",  # Green
                                        'mid_color': "#FFEB84",  # Yellow
                                        'max_color': "#F8696B",  # Red
                                        'value': 0}

        slat_array = self.generate_slat_occupancy_grid()
        handle_array = self.generate_assembly_handle_grid()

        # prepares and writes out slat arrays
        for layer in range(len(self.layer_palette)):
            slat_df = pd.DataFrame(np.zeros(shape=(slat_array.shape[0], slat_array.shape[1])))
            for key, slat in self.slats.items():
                if not slat.non_assembly_slat and slat.layer == layer + 1:  # only writes out slats that are in the current layer
                    for posn in range(32):
                        y, x = slat.slat_position_to_coordinate[posn+1]
                        slat_df.iloc[y, x] = f"{slat.ID.split('slat')[-1]}-{posn+1}"

            slat_df.to_excel(writer, sheet_name=f'slat_layer_{layer+1}', index=False,header=False)
            # color all non-zero cells with the layer color
            worksheet = writer.sheets[f'slat_layer_{layer+1}']
            # Convert hex like '#FFCC00' to xlsxwriter format
            hex_color = self.layer_palette[layer+1]['color'].lstrip('#')
            # Define cell format with background color
            cell_format = workbook.add_format({'bg_color': f'#{hex_color}'})
            # Apply format to non-empty cells
            for row in range(slat_df.shape[0]):
                for col in range(slat_df.shape[1]):
                    value = slat_df.iat[row, col]
                    if value not in (0, 0.0, '', None):
                        worksheet.write(row, col, value, cell_format)

        # writes out handle arrays
        if np.sum(handle_array) > 0:
            write_array_to_excel(writer, handle_array, 'handle_interface')

        # prepares and sorts cargo dataframes
        cargo_dfs = {}
        seed_dfs = {}
        for layer in range(len(self.layer_palette)):
            for orientation in [2, 5]:
                desc_string = 'upper' if  self.layer_palette[layer+1]['top'] == orientation else 'lower'
                cargo_dfs[f'cargo_layer_{layer+1}_{desc_string}_h{orientation}'] = pd.DataFrame(np.zeros(shape=(slat_array.shape[0], slat_array.shape[1])))
                seed_dfs[f'seed_layer_{layer+1}_{desc_string}_h{orientation}'] = pd.DataFrame(np.zeros(shape=(slat_array.shape[0], slat_array.shape[1])))

        for key, slat in self.slats.items():
            for side in [2, 5]:
                for handle_position, handle_data in slat.get_sorted_handles('h%s' % side):
                    if 'CARGO' == handle_data['category']:
                        y, x = slat.slat_position_to_coordinate[handle_position]
                        if self.layer_palette[slat.layer]['top'] == side:
                            handle_layer = 'upper'
                        else:
                            handle_layer = 'lower'
                        cargo_dfs[f'cargo_layer_{slat.layer}_{handle_layer}_h{side}'].iloc[y, x] = handle_data['value']
                    elif 'SEED' == handle_data['category']:
                        y, x = slat.slat_position_to_coordinate[handle_position]
                        if self.layer_palette[slat.layer]['top'] == side:
                            handle_layer = 'upper'
                        else:
                            handle_layer = 'lower'
                        seed_id = handle_data['descriptor'].split('|')[-1]
                        seed_dfs[f'seed_layer_{slat.layer}_{handle_layer}_h{side}'].iloc[y, x] = f'%s-%s' % (seed_id, handle_data['value'].replace('_', '-'))

        for key, val in {**cargo_dfs, **seed_dfs}.items():
            # if df is full of zeros, skip writing it to excel (to reduce file complexity)
            if not ((val != 0) & (val != "0")).any().any():
                continue
            val.to_excel(writer, sheet_name=key, index=False,header=False)
            writer.sheets[key].conditional_format(0, 0, val.shape[0], val.shape[1] - 1, excel_conditional_formatting)

        # prints out essential metadata required to regenerate design or import into #-CAD
        layer_interface_orientations = export_layer_orientations_to_list_format(self.layer_palette)
        layer_info_columns = ["ID", "Default Rotation", "Top Helix", "Bottom Helix", "Next Slat ID", "Slat Count", "Colour"]
        layer_output_dict = {}
        for layer in range(1, len(self.layer_palette) + 1):
            slat_count = len(np.unique(slat_array[..., layer - 1][slat_array[..., layer - 1] != 0]))
            layer_output_dict[self.layer_palette[layer]['ID']] = [
                                        120 if self.connection_angle == '60' else 90,
                                        'H%s' % self.layer_palette[layer]['top'],
                                        'H%s' % self.layer_palette[layer]['bottom'],
                                        np.max(slat_array[..., layer-1]) + 1,
                                        slat_count,
                                        self.layer_palette[layer]['color']]

        cargo_output_dict = {}
        for c_key, c_val in self.cargo_palette.items():
            cargo_output_dict[c_key] = [c_val['short name'], c_val['color']]

        color_output_dict = {}
        for slat_id, slat in self.slats.items():
            if slat.unique_color is not None:
                color_output_dict[f'{self.layer_palette[slat.layer]["ID"].split(" ")[-1]}-I{slat.ID.split("slat")[-1]}'] = [slat.unique_color]

        metadata = pd.DataFrame.from_dict({'Layer Interface Orientations': [layer_interface_orientations],
                                           'Connection Angle': [self.connection_angle],
                                           'File Format': ['#-CAD'],
                                           'Canvas Offset (Min)': list(self.hashcad_canvas_metadata['canvas_offset_min']),
                                           'Canvas Offset (Max)': list(self.hashcad_canvas_metadata['canvas_offset_max']),
                                           'LAYER INFO': [''],
                                           'ID':layer_info_columns[1:],
                                           **layer_output_dict,
                                           'CARGO INFO': [''],
                                           'ID ':['Short Name', 'Colour'],
                                           **cargo_output_dict,
                                           'UNIQUE SLAT COLOUR INFO': [''],
                                           'ID  ': ['Colour'],
                                           **color_output_dict}, orient='index')
        metadata.reset_index(inplace=True)

        metadata.to_excel(writer, index=False, header=False, sheet_name="metadata")
        workbook = writer.book
        worksheet = writer.sheets["metadata"]

        # Merge and center first 6 columns of row 6 (Excel is 1-indexed, so row 7)
        merge_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
        })

        worksheet.merge_range('A6:G6', 'LAYER INFO', merge_format)
        worksheet.merge_range(f'A{8+len(layer_output_dict)}:G{8+len(layer_output_dict)}', 'CARGO INFO', merge_format)
        worksheet.merge_range(f'A{10+len(layer_output_dict) + len(cargo_output_dict)}:G{10+len(layer_output_dict) + len(cargo_output_dict)}', 'UNIQUE SLAT COLOUR INFO', merge_format)

        # Adjust column widths
        for col_idx in range(metadata.shape[1]):
            max_len = 0
            for row in range(metadata.shape[0]):
                val = metadata.iloc[row, col_idx]
                if val is not None and not (isinstance(val, float) and pd.isna(val)):
                    max_len = max(max_len, len(str(val)))
            worksheet.set_column(col_idx, col_idx, max_len + 2)

        # finally, print out the slat_types worksheet
        slat_type_output_dict = defaultdict(list)
        for key, slat in self.slats.items():
            slat_type_output_dict['Layer'].append(slat.layer)
            slat_type_output_dict['Slat ID'].append(int(slat.ID.split("slat")[-1]))
            slat_type_output_dict['Type'].append(slat.slat_type)
        slat_type_df = pd.DataFrame.from_dict(slat_type_output_dict)
        slat_type_df.to_excel(writer, index=False, header=True, sheet_name="slat_types")

        writer.close()

    def import_design(self, file):
        """
        Reads in a complete megastructure from an excel file formatted with each array separated in a different sheet.
        :param file: Path to Excel file containing megastructure design
        :return: All arrays and metadata necessary to regenerate the design
        """

        design_df = pd.read_excel(file, sheet_name=None, header=None)
        layer_count = 0

        for i, key in enumerate(design_df.keys()):
            if 'slat_layer_' in key:
                layer_count += 1

        # preparing and reading in slat/handle arrays
        slat_array = np.zeros((design_df['slat_layer_1'].shape[0], design_df['slat_layer_1'].shape[1], layer_count))
        slat_grid_coords = (slat_array.shape[0], slat_array.shape[1])

        handle_array_available = any('handle' in string for string in list(design_df.keys()))

        old_file_format = True

        if handle_array_available:
            handle_array = np.zeros((design_df['slat_layer_1'].shape[0], design_df['slat_layer_1'].shape[1], layer_count - 1))
        else:
            handle_array = None

        # reading in slat types (if available, older files did not have this sheet)
        if 'slat_types' in design_df:
            slat_type_df = design_df['slat_types']
            slat_type_df.columns = slat_type_df.iloc[0]  # first row becomes column names
            slat_type_df = slat_type_df.drop(0).reset_index(drop=True)
            slat_type_dict = {(int(row["Layer"]), int(row["Slat ID"])): row["Type"] for _, row in slat_type_df.iterrows()}
            # not all slats have to be defined here, those that aren't will be assumed to be tubes
        else:
            # if no slat types are defined, assume all slats are of type 'tube'
            slat_type_dict = {}

        slats = {}
        for i in range(layer_count):
            # in the new system, slat elements are stored in the form ID-POSN which allows for the exact orientation of slats (even reversed directions and so on)
            slat_data = design_df['slat_layer_%s' % (i + 1)].values
            if np.any(np.vectorize(lambda x: isinstance(x, str))(slat_data)):
                old_file_format = False
                slat_coords = defaultdict(dict)
                for row in range(slat_data.shape[0]):
                    for col in range(slat_data.shape[1]):
                        cell = slat_data[row, col] # gathers slat positions and coordinates directly from each cell
                        if isinstance(cell, str) and '-' in cell:
                            id_part, posn_part = cell.split('-', 1)
                            slat_coords[id_part][int(posn_part)] = (row, col)
                for slat_id, coords in slat_coords.items(): # generate a slat from each ID found in the file
                    slats[get_slat_key(i + 1, int(slat_id))] = Slat(get_slat_key(i + 1, int(slat_id)), i + 1, coords,
                                                                    slat_type=slat_type_dict[i+1, int(slat_id)] if (i+1, int(slat_id)) in slat_type_dict else 'tube')
            else:
                slat_array[..., i] = slat_data  # if using the old system, slat data is just a 2D array of slat IDs, from which a direction is defined as travelling from top to bottom by default

            if i != layer_count - 1 and handle_array_available:
                handle_array[..., i] = design_df['handle_interface_%s' % (i + 1)].values

        if old_file_format:
            slats = convert_slat_array_into_slat_objects(slat_array)

        # sort slats based on their ID
        slats = {k: v for k, v in sorted(slats.items(), key=lambda item: natural_sort_key(item[0]))}

        # reading in cargo arrays and transferring to a dictionary
        cargo_dict = {}
        seed_dict = defaultdict(list)
        for i, key in enumerate(design_df.keys()):
            if 'cargo' in key:
                layer = int(key.split('_')[2]) # e.g. cargo_layer_1_upper_h2
                orientation = int(key.split('_')[4][-1])
                cargo_array = design_df[key].values
                cargo_coords = np.where(cargo_array != 0)  # only extracts a value if there is cargo present, reducing clutter
                for y, x in zip(cargo_coords[0], cargo_coords[1]):
                    cargo_dict[((int(y), int(x)), layer, orientation)] = cargo_array[y, x]
            if 'seed' in key:
                if 'h' not in key:
                    print(Fore.RED + f'WARNING: Seed from imported file was not read in - please check format.')
                    break
                layer = int(key.split('_')[2])  # e.g. seed_layer_1_upper_h2
                orientation = int(key.split('_')[4][-1])
                seed_coords = np.where(design_df[key].values != 0)  # only extracts a value if there is seed present, reducing clutter
                for y, x in zip(seed_coords[0], seed_coords[1]):
                    position_id = design_df[key].values[y, x]
                    if isinstance(position_id, int):
                        print(Fore.RED + f'WARNING: Seed from imported file was not read in - please check format.')
                        break
                    seed_id = position_id.split('-')[0]
                    seed_handle = position_id.split('-', 1)[1].replace('-', '_')
                    seed_dict[(seed_id, layer, orientation)].append((y, x, seed_handle))

        # extracts and formats metadata
        metadata = design_df.get('metadata')
        if metadata is None:
            raise ValueError("Missing required 'metadata' sheet.")

        metadata.set_index(metadata.columns[0], inplace=True)
        layer_interface_orientations = ast.literal_eval(metadata.loc['Layer Interface Orientations'].iloc[0])
        connection_angle = metadata.loc['Connection Angle'].iloc[0]

        # parse layer and cargo palettes from metadata
        layer_palette = create_default_layer_palette(layer_interface_orientations)
        cargo_palette = {}

        try:
            layer_info_start = metadata.index.get_loc('LAYER INFO') + 2
            # Read until the next empty row or section for LAYER INFO
            for ind, i in enumerate(range(layer_info_start, len(metadata))):
                row = metadata.iloc[i]
                if pd.isna(row[1]):
                    break
                layer_palette[ind+1]['color'] = row[6]
                layer_palette[ind+1]['ID'] = row.name
        except:
            print(Fore.RED + 'No layer palette found in metadata, using default colors.' + Fore.RESET)

        try:
            cargo_info_start = metadata.index.get_loc('CARGO INFO') + 2
            # Read until the next empty row or section for CARGO INFO
            for i in range(cargo_info_start, len(metadata)):
                row = metadata.iloc[i]
                if pd.isna(row[1]):
                    break
                cargo_palette[metadata.index[i]] = {'short name': row[1], 'color': row[2]}
        except:
            print(Fore.RED + 'No cargo palette found in metadata, using default colors.' + Fore.RESET)

        if 'SEED' not in cargo_palette:
            cargo_palette['SEED'] = {'short name': 'S1', 'color': '#FF0000'}

        try:
            color_info_start = metadata.index.get_loc('UNIQUE SLAT COLOUR INFO') + 2
            # reads in and applies unique slat colors if present
            unique_slat_color_palette = {}
            # Read until the next empty row or section for COLOR INFO
            for ind, i in enumerate(range(color_info_start, len(metadata))):
                row = metadata.iloc[i]
                if pd.isna(row[1]):
                    break
                s_layer = 'Layer ' + row.name.split('-')[0]
                s_num = row.name.split('-I')[1]
                # get layer index from layer_palette by matching ID
                s_layer_index = None
                for l_index, l_info in layer_palette.items():
                    if l_info['ID'] == s_layer:
                        s_layer_index = l_index
                        break
                unique_slat_color_palette[get_slat_key(s_layer_index, s_num)] = row[1]

            for slat in slats.values():
                if slat.ID in unique_slat_color_palette:
                    slat.unique_color = unique_slat_color_palette[slat.ID]
                slat.layer_color = layer_palette[slat.layer]['color']
        except:
            print(Fore.RED + 'No unique slat color palette found in metadata, using default colors.' + Fore.RESET)
        try:
            canvas_min_pos = metadata.index.get_loc('Canvas Offset (Min)')
            canvas_max_pos = metadata.index.get_loc('Canvas Offset (Max)')
            canvas_min = tuple(float(m) for m in metadata.iloc[canvas_min_pos].values[0:2])
            canvas_max = tuple(float(m) for m in metadata.iloc[canvas_max_pos].values[0:2])
            hashcad_canvas_metadata = {'canvas_offset_min': canvas_min, 'canvas_offset_max':canvas_max}
        except:
            hashcad_canvas_metadata = {'canvas_offset_min': (0.0, 0.0), 'canvas_offset_max':(0.0, 0.0)}

        # sets default colors from layer map
        for slat in slats.values():
            slat.layer_color = layer_palette[slat.layer]['color']

        return slats, handle_array, seed_dict, cargo_dict, connection_angle, layer_palette, cargo_palette, hashcad_canvas_metadata, slat_grid_coords


if __name__ == '__main__':
    # testing a typical megastructure import
    design_file = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/hash_cad_validation_designs/lily/lily_design_hashcad_seed.xlsx'
    design_file = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/hash_cad_validation_designs/bird/bird_design_hashcad_seed.xlsx'
    design_file = '/Users/matt/Desktop/T2.xlsx'

    megastructure = Megastructure(import_design_file=design_file)

    from crisscross.plate_mapping import *

    main_plates = get_cutting_edge_plates()
    cargo_plates = get_cargo_plates()
    all_plates = main_plates + cargo_plates
    megastructure.patch_placeholder_handles(all_plates)
    megastructure.patch_flat_staples(main_plates[0])

    echo_sheet_1 = convert_slats_into_echo_commands(slat_dict=megastructure.slats,
                                                    destination_plate_name='TEST',
                                                    reference_transfer_volume_nl=50,
                                                    output_folder='/Users/matt/Desktop',
                                                    center_only_well_pattern=False,
                                                    plate_viz_type='barcode',
                                                    output_filename=f'TST_echo_commands.csv')

    # hamming_results = multirule_oneshot_hamming(megastructure.generate_slat_occupancy_grid(), megastructure.generate_assembly_handle_grid(), request_substitute_risk_score=True)
    # print('Hamming distance from imported array: %s, Duplication Risk: %s' % (hamming_results['Universal'], hamming_results['Substitute Risk']))
    # megastructure.create_standard_graphical_report('/Users/matt/Desktop/test_graphics')
    # megastructure.create_blender_3D_view('/Users/matt/Desktop', camera_spin=False, correct_slat_entrance_direction=True, include_bottom_light=False)
    # megastructure.export_design('TEST.xlsx', '/Users/matt/Desktop')
