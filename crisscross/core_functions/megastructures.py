import copy
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt
from colorama import Fore
import os
import matplotlib as mpl
import pandas as pd
import ast

from crisscross.core_functions.slats import get_slat_key, convert_slat_array_into_slat_objects
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.slat_salient_quantities import connection_angles
from crisscross.graphics.static_plots import create_graphical_slat_view, create_graphical_assembly_handle_view
from crisscross.graphics.pyvista_3d import create_graphical_3D_view
from crisscross.graphics.blender_3d import create_graphical_3D_view_bpy

plt.rcParams.update({'font.sans-serif': 'Helvetica'})  # consistent figure formatting


class Megastructure:
    """
    Convenience class that bundles the entire details of a megastructure including slat positions, seed handles and cargo.
    """

    def __init__(self, slat_array=None, layer_interface_orientations=None, connection_angle='90',
                 import_design_file=None):
        """
        :param slat_array: Array of slat positions (3D - X,Y, layer ID) containing the positions of all slats in the design.
        :param layer_interface_orientations: The direction each slat will be facing in the design.
        :param connection_angle: The angle at which the slats will be connected.  For now, only 90 and 60 grids are supported.
        E.g. for a 2 layer design, [2, 5, 2] implies that the bottom layer will have H2 handles sticking out,
        the connecting interface will have H5 handles and the top layer will have H2 handles again.
        TODO: how to enforce slat length?  Will this need to change in the future?
        TODO: how do we consider the additional 12nm/6nm on either end of the slat?
        """

        # reads in all design details from file if available
        if import_design_file is not None:
            slat_array, handle_array, seed_array, cargo_df, layer_interface_orientations, connection_angle, reversed_slats \
                = self.import_design(import_design_file)
            self.handle_arrays = handle_array
            self.cargo_dict = cargo_df
            self.seed_array = seed_array
        else:
            if slat_array is None:
                raise RuntimeError(
                    'A slat array must be provided to initialize the megastructure (either imported or directly).')
            self.handle_arrays = None
            self.seed_array = None
            self.cargo_dict = {}
            reversed_slats = None

        self.slats = {}
        self.slat_array = slat_array
        self.num_layers = slat_array.shape[2]
        self.connection_angle = connection_angle

        if connection_angle not in ['60', '90']:
            raise NotImplementedError('Only 90 and 60 degree connection angles are supported.')

        # these are the grid distance jump per point, which can be different for the x/y directions
        self.grid_xd = connection_angles[connection_angle][0]
        self.grid_yd = connection_angles[connection_angle][1]

        # if no custom interface supplied, assuming alternating H2/H5 handles,
        # with H2 at the bottom, H5 at the top, and alternating connections in between
        # e.g. for a 3-layer structure, layer_interface_orientations = [2, (5, 2), (5,2), 5]
        if layer_interface_orientations is None:
            self.layer_interface_orientations = [2] + [(5, 2)] * (self.num_layers - 1) + [5]
        else:
            self.layer_interface_orientations = layer_interface_orientations

        self.slats = convert_slat_array_into_slat_objects(slat_array)

        if reversed_slats is not None:
            for slat in reversed_slats:
                self.slats[slat].reverse_direction()

        # if design file was provided, the seed, handles and cargo can be pre-assigned here
        if self.seed_array is not None:
            self.assign_seed_handles(self.seed_array[1], layer_id=self.seed_array[0])
        if self.handle_arrays is not None:
            self.assign_crisscross_handles(self.handle_arrays)
        if len(self.cargo_dict) > 0:
            self.assign_cargo_handles_with_dict(self.cargo_dict)

    def assign_crisscross_handles(self, handle_arrays, crisscross_handle_plates=None,
                                  crisscross_antihandle_plates=None):
        """
        Assigns crisscross handles to the slats based on the handle arrays provided.
        :param handle_arrays: 3D array of handle values (X, Y, layer) where each value corresponds to a handle ID.
        :param crisscross_handle_plates: Crisscross handle plates.  If not supplied, a placeholder will be added to the slat instead.
        :param crisscross_antihandle_plates: Crisscross anti-handle plates.  If not supplied, a placeholder will be added to the slat instead.
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
                slat_crisscross_interfaces.extend([self.layer_interface_orientations[slat.layer - 1][1],
                                                   self.layer_interface_orientations[slat.layer][0]])
                handle_layers.extend([slat.layer - 2, slat.layer - 1])
                handle_plates.extend([crisscross_antihandle_plates,
                                      crisscross_handle_plates])  # handle orientation always assumed to follow same pattern

            for slat_position_index in range(slat.max_length):
                coords = slat.slat_position_to_coordinate[slat_position_index + 1]
                for layer, slat_side, sel_plates in zip(handle_layers, slat_crisscross_interfaces, handle_plates):
                    handle_val = int(handle_arrays[coords[0], coords[1], layer])
                    if handle_val < 1:  # no crisscross handles here
                        continue
                    if sel_plates is None:  # no plate supplied, so a placeholder is defined instead
                        self.slats[key].set_placeholder_handle(slat_position_index + 1, slat_side,
                                                               descriptor='Placeholder-Assembly-%s' % handle_val)
                    else:  # extracts the sequence and plate well for the specific position requested
                        self.slats[key].set_handle(slat_position_index + 1, slat_side,
                                                   sel_plates.get_sequence(slat_position_index + 1, slat_side,
                                                                           handle_val),
                                                   sel_plates.get_well(slat_position_index + 1, slat_side, handle_val),
                                                   sel_plates.get_plate_name(slat_position_index + 1, slat_side,
                                                                             handle_val),
                                                   descriptor='Ass. Handle %s, Plate %s' % (handle_val,
                                                                                            sel_plates.get_plate_name(
                                                                                                slat_position_index + 1,
                                                                                                slat_side, handle_val)))

    def assign_seed_handles(self, seed_array, seed_plate=None, layer_id=1):
        """
        Assigns seed handles to the slats based on the seed array provided.
        :param seed_array: 2D array with positioning of seed.  Each row of the seed should have a unique ID.
        :param seed_plate: Plate class with sequences to draw from.  If not provided, a placeholder will be added
         to the slat instead.
        """

        seed_coords = np.where(seed_array > 0)
        # TODO: more checks to ensure seed placement fits all parameters?
        for y, x in zip(seed_coords[0], seed_coords[1]):

            slat_ID = self.slat_array[y, x, layer_id - 1]
            if slat_ID == 0:
                raise RuntimeError('There is a seed coordinate placed on a non-slat position.  '
                                   'Please re-verify your seed pattern array.')

            selected_slat = self.slats[get_slat_key(layer_id, slat_ID)]
            slat_position = selected_slat.slat_coordinate_to_position[(y, x)]
            seed_value = int(seed_array[y, x])

            if layer_id == 1:
                bottom_slat_side = self.layer_interface_orientations[0]
            else:
                bottom_slat_side = self.layer_interface_orientations[layer_id - 1][1]

            if bottom_slat_side == 5:
                raise NotImplementedError('Seed placement on H5 side not yet supported.')

            if seed_plate is not None:
                if not isinstance(seed_plate.get_sequence(slat_position, 2, seed_value), str):
                    raise RuntimeError('Seed plate selected cannot support placement on canvas.')

                selected_slat.set_handle(slat_position, bottom_slat_side,
                                         seed_plate.get_sequence(slat_position, 2, seed_value),
                                         seed_plate.get_well(slat_position, 2, seed_value),
                                         seed_plate.get_plate_name(),
                                         descriptor='Seed Handle, Plate %s' % seed_plate.get_plate_name())
            else:
                selected_slat.set_placeholder_handle(slat_position, bottom_slat_side,
                                                     descriptor='Placeholder-Seed-%s' % seed_value)

        if len(seed_coords[0]) == 0:
            print((Fore.RED + 'WARNING: No seed handles were set - is your seed pattern array correct?'))

        self.seed_array = (layer_id, seed_array)

    def assign_cargo_handles_with_dict(self, cargo_dict, cargo_plate=None):
        """
        Assigns cargo handles to the megastructure slats based on the cargo dictionary provided.
        :param cargo_dict: Dictionary of cargo placements (key = slat position, layer, handle orientation, value = cargo ID)
        :param cargo_plate: The cargo plate from which cargo will be assigned.  If not provided, a placeholder will be assigned instead.
        :return: N/A
        """

        for key, cargo_value in cargo_dict.items():
            y_pos = key[0][0]
            x_pos = key[0][1]
            layer = key[1]
            handle_orientation = key[2]
            slat_ID = self.slat_array[y_pos, x_pos, layer - 1]

            if slat_ID == 0:
                raise RuntimeError('There is a cargo coordinate placed on a non-slat position.  '
                                   'Please re-verify your cargo pattern array.')

            selected_slat = self.slats[get_slat_key(layer, slat_ID)]
            slat_position = selected_slat.slat_coordinate_to_position[(y_pos, x_pos)]

            if cargo_plate is not None:
                if not isinstance(cargo_plate.get_sequence(slat_position, handle_orientation, cargo_value), str):
                    raise RuntimeError('Cargo plate selected cannot support placement on canvas.')

                selected_slat.set_handle(slat_position, handle_orientation,
                                         cargo_plate.get_sequence(slat_position, handle_orientation, cargo_value),
                                         cargo_plate.get_well(slat_position, handle_orientation, cargo_value),
                                         cargo_plate.get_plate_name(),
                                         descriptor='Cargo Plate %s, Handle %s' % (
                                             cargo_plate.get_plate_name(), cargo_value))
            else:
                selected_slat.set_placeholder_handle(slat_position, handle_orientation,
                                                     descriptor='Placeholder-Cargo-%s' % cargo_value)
        self.cargo_dict = {**self.cargo_dict, **cargo_dict}

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
            layer = self.num_layers
            if handle_orientation:
                raise RuntimeError('Handle orientation cannot be specified when '
                                   'placing cargo at the top of the design.')
            handle_orientation = self.layer_interface_orientations[-1]

        elif layer == 'bottom':
            layer = 1
            if handle_orientation:
                raise RuntimeError('Handle orientation cannot be specified when '
                                   'placing cargo at the top of the design.')
            handle_orientation = self.layer_interface_orientations[0]
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
        :param cargo_plate: Plate class with sequences to draw from.  If not provided, a placeholder will be assigned instead.
        :param cargo_key: Dictionary mapping cargo IDs to cargo unique names for proper identification.
        :param layer: Either 'top' or 'bottom', or the exact layer ID required.
        :param handle_orientation: If a middle layer is specified,
        then the handle orientation must be provided since there are always two options available.
        """
        cargo_dict = self.convert_cargo_array_into_cargo_dict(cargo_array, cargo_key, layer=layer,
                                                              handle_orientation=handle_orientation)
        self.assign_cargo_handles_with_dict(cargo_dict, cargo_plate)

    def patch_placeholder_handles(self, plates, plate_types):
        """
        Patches placeholder handles with actual handles based on the plates provided.
        :param plates: List of plates from which to extract handles.
        :param plate_types: List of associated plate types for each plate provided.
        :return: N/A
        """
        for key, slat in self.slats.items():
            placeholder_list = copy.copy(slat.placeholder_list)
            for placeholder_handle in placeholder_list:  # runs through all placeholders on current slat
                handle = int(
                    placeholder_handle.split('-')[1])  # extracts handle, orientation and cargo ID from placeholder
                orientation = int(placeholder_handle.split('-')[-1][1:])

                if orientation == 2:
                    cargo_value = slat.H2_handles[handle]['descriptor']
                else:
                    cargo_value = slat.H5_handles[handle]['descriptor']

                cargo_type = cargo_value.split('-')[
                    1]  # the placeholder name is always defined with the same pattern of -s
                cargo_id = cargo_value.split('-')[-1]
                if cargo_id.isnumeric():
                    cargo_id = int(cargo_id)

                # the assembly handles can be either handles or antihandles, which can be identified from
                # the design layer interface orientations
                if cargo_type == 'Assembly':
                    if slat.layer == self.num_layers:
                        slat_top_orientation = self.layer_interface_orientations[-1]
                    else:
                        slat_top_orientation = self.layer_interface_orientations[slat.layer][0]

                    if orientation == slat_top_orientation:
                        cargo_type = cargo_type + '-Handles'
                    else:
                        cargo_type = cargo_type + '-AntiHandles'

                # if a plate has a match to the placeholder, extract the handle info and assign to the slat
                for plate, plate_type in zip(plates, plate_types):
                    if plate_type == cargo_type:
                        if not isinstance(plate.get_sequence(handle, orientation, cargo_id), bool):
                            sequence = plate.get_sequence(handle, orientation, cargo_id)
                            well = plate.get_well(handle, orientation, cargo_id)
                            name = plate.get_plate_name(handle, orientation, cargo_id)
                            slat.update_placeholder_handle(handle, orientation, sequence, well, name,
                                                           descriptor=f'{cargo_type}-{cargo_id}')
            if len(slat.placeholder_list) > 0:
                print(Fore.RED + f'WARNING: Placeholder handles on slat {key} still remain after patching.')

    def patch_control_handles(self, control_plate):
        """
        Fills up all remaining holes in slats with no-handle control sequences.
        :param control_plate: Plate class with core sequences to draw from.
        """
        for key, slat in self.slats.items():
            for i in range(1, slat.max_length + 1):
                if i not in slat.H2_handles:
                    slat.set_handle(i, 2,
                                    control_plate.get_sequence(i, 2, 0),
                                    control_plate.get_well(i, 2, 0),
                                    control_plate.get_plate_name(),
                                    descriptor='Control Handle')
                if i not in slat.H5_handles:
                    slat.set_handle(i, 5,
                                    control_plate.get_sequence(i, 5, 0),
                                    control_plate.get_well(i, 5, 0),
                                    control_plate.get_plate_name(),
                                    descriptor='Control Handle')

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
        for s_key, s_val in self.slats.items():
            if s_val.layer < 1 or s_val.layer > self.num_layers:  # these slats can never be rationally identified, and should be animated in last
                special_slats.append(s_val.ID)
                rational_slat_count -= 1

        while slat_count < rational_slat_count:  # will loop through the design until all slats have been given a home
            if slat_count == 0:  # first extracts slats that will attach to the seed
                first_step_slats = set()
                seed_coords = np.where(self.seed_array[1] > 0)
                for y, x in zip(seed_coords[0],
                                seed_coords[1]):  # extracts the slat ids from the layer connecting to the seed
                    overlapping_slat = (self.seed_array[0], self.slat_array[y, x, self.seed_array[0] - 1])
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
                        slat_posns = np.where(self.slat_array[..., layer - 1] == slat)
                        for y, x in zip(slat_posns[0], slat_posns[1]):
                            if layer != 1 and self.slat_array[y, x, layer - 2] != 0:  # checks the layer below
                                slat_overlap_counts[(layer - 1, self.slat_array[y, x, layer - 2])] += 1
                            if layer != self.num_layers and self.slat_array[y, x, layer] != 0:  # checks the layer above
                                slat_overlap_counts[(layer + 1, self.slat_array[y, x, layer])] += 1
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

    def create_graphical_slat_view(self, save_to_folder=None, instant_view=True,
                                   include_cargo=True, include_seed=True,
                                   colormap='Set1', seed_color=(1.0, 0.0, 0.0), cargo_colormap='Set1'):
        """
        Creates a graphical view of the slats, cargo and seeds in the design.  Refer to the graphics module for more details.
        :param save_to_folder: Set to the filepath of a folder where all figures will be saved.
        :param instant_view: Set to True to plot the figures immediately to your active view.
        :param include_cargo: Set to True to include cargo in the graphical view.
        :param include_seed: Set to True to include the seed in the graphical view.
        :param colormap: The colormap to sample from for each additional layer.
        :param seed_color: The color of the seed in the design.
        :param cargo_colormap: The colormap to sample from for each cargo type.
        :return: N/A
        """

        create_graphical_slat_view(self.slat_array,
                                   layer_interface_orientations=self.layer_interface_orientations,
                                   slats=self.slats, seed_array=self.seed_array if include_seed else None,
                                   cargo_dict=self.cargo_dict if include_cargo else None,
                                   save_to_folder=save_to_folder, instant_view=instant_view,
                                   connection_angle=self.connection_angle,
                                   colormap=colormap, seed_color=seed_color,
                                   cargo_colormap=cargo_colormap)

    def create_graphical_assembly_handle_view(self, save_to_folder=None, instant_view=True, colormap='Set1'):
        """
        Creates a graphical view of the assembly handles in the design.  Refer to the graphics module for more details.
        :param save_to_folder: Set to the filepath of a folder where all figures will be saved.
        :param instant_view: Set to True to plot the figures immediately to your active view.
        :param colormap: The colormap to sample from for each additional layer.
        :return: N/A
        """

        if self.handle_arrays is None:
            print(Fore.RED + 'No handle graphics will be generated as no handle arrays have been assigned to the design.')
            return

        create_graphical_assembly_handle_view(self.slat_array, self.handle_arrays,
                                              layer_interface_orientations=self.layer_interface_orientations,
                                              slats=self.slats, save_to_folder=save_to_folder,
                                              connection_angle=self.connection_angle,
                                              instant_view=instant_view, colormap=colormap)

    def create_graphical_slat_views(self, save_folder, colormap='Set1'):
        """
        Creates individual graphical view of each slat in the design.
        :param save_folder: Folder to save all slat images to.
        :param colormap: Colormap to extract layer colors from
        :return: N/A
        """

        output_folder = os.path.join(save_folder, 'individual_slat_graphics')
        create_dir_if_empty(output_folder)
        for slat_id, slat in self.slats.items():
            l_fig, l_ax = plt.subplots(1, 1, figsize=(20, 9))
            plt.title('Detailed View of Slat with ID %s' % slat_id, fontsize=35)
            l_ax.set_ylim(0, 10)
            l_ax.set_xlim(-1, 32)
            l_ax.axis('off')
            if isinstance(slat.layer, int):
                slat_color = mpl.colormaps[colormap].colors[slat.layer - 1]
            else:
                slat_color = 'black'

            plt.plot([0, 31], [2, 2], color=slat_color, linewidth=15, zorder=5)
            plt.text(-0.7, 2.5, 'H2', color='black',
                     fontsize=25, weight='bold', ha='center', va='center')
            plt.text(-0.7, 1.5, 'H5', color='black',
                     fontsize=25, weight='bold', ha='center', va='center')

            for i in range(32):
                h2_handle = slat.H2_handles[i + 1]
                h5_handle = slat.H5_handles[i + 1]

                plt.text(i, 3.5, h2_handle['descriptor'], color='black', zorder=3, ha='center',
                         fontsize=15, weight='bold', rotation='vertical')
                plt.text(i, 0.5, h5_handle['descriptor'], color='black', zorder=3, ha='center',
                         va='top', fontsize=15, weight='bold', rotation='vertical')

                plt.plot([i, i], [2, 3], color='black', linewidth=12, zorder=1)
                plt.plot([i, i], [2, 1], color='black', linewidth=12, zorder=1)

            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, '%s.png' % slat_id), dpi=300)
            plt.close(l_fig)

    def create_graphical_3D_view(self, save_folder, window_size=(2048, 2048), colormap='Set1',
                                 cargo_colormap='Dark2', seed_color=(1.0, 0.0, 0.0)):
        """
        Creates a 3D video of the megastructure slat design.
        :param save_folder: Folder to save all video to.
        :param window_size: Resolution of video generated.  2048x2048 seems reasonable in most cases.
        :param colormap: Colormap to extract layer colors from
        :param cargo_colormap: Colormap to extract cargo colors from
        :param seed_color: Color of the seed in the design.
        :return: N/A
        """
        create_graphical_3D_view(self.slat_array, save_folder, slats=self.slats, connection_angle=self.connection_angle,
                                 cargo_dict=self.cargo_dict, cargo_colormap=cargo_colormap,
                                 layer_interface_orientations=self.layer_interface_orientations,
                                 seed_color=seed_color, seed_layer_and_array=self.seed_array,
                                 window_size=window_size, colormap=colormap)

    def create_blender_3D_view(self, save_folder, animate_assembly=False, animation_type='translate',
                               custom_assembly_groups=None, slat_translate_dict=None, minimum_slat_cutoff=15,
                               camera_spin=False, correct_slat_entrance_direction=True, colormap='Set1',
                               cargo_colormap='Dark2', seed_color=(1, 0, 0)):
        """
        Creates a 3D model of the megastructure slat design as a Blender file.
        :param save_folder: Folder to save all video to.
        :param animate_assembly: Set to true to also generate an animation of the design being assembled group by group
        :param custom_assembly_groups: If set, will use the specific provided dictionary to assign slats to the animation order.
        :param slat_translate_dict: If set, will use the specific provided dictionary to assign specific
        animation translation distances to each slat.
        :param minimum_slat_cutoff: Minimum number of slats that need to be present for a slat to be considered stable.
        You might want to vary this number as certain designs have staggers that don't allow for a perfect 16-slat binding system.
        :param camera_spin: Set to true to have camera spin around object during the animation.
        :param correct_slat_entrance_direction: If set to true, will attempt to correct the slat entrance animation to
        always start from a place that is supported.
        :param colormap: Colormap to extract layer colors from
        :param cargo_colormap: Colormap to extract cargo colors from
        :param seed_color: Color of the seed in the design.
        :return: N/A
        """
        if animate_assembly:
            if custom_assembly_groups:
                assembly_groups = custom_assembly_groups
            else:
                assembly_groups = self.get_slats_by_assembly_stage(minimum_handle_cutoff=minimum_slat_cutoff)
        else:
            assembly_groups = None

        create_graphical_3D_view_bpy(self.slat_array, save_folder, slats=self.slats,
                                     seed_layer_and_array=self.seed_array,
                                     animate_slat_group_dict=assembly_groups,
                                     connection_angle=self.connection_angle,
                                     animation_type=animation_type, camera_spin=camera_spin,
                                     correct_slat_entrance_direction=correct_slat_entrance_direction,
                                     seed_color=seed_color, colormap=colormap, cargo_colormap=cargo_colormap,
                                     layer_interface_orientations=self.layer_interface_orientations,
                                     cargo_dict=self.cargo_dict,
                                     specific_slat_translate_distances=slat_translate_dict)

    def create_standard_graphical_report(self, output_folder, draw_individual_slat_reports=False,
                                         generate_3d_video=True,
                                         colormap='Dark2', cargo_colormap='Set1', seed_color=(1.0, 0.0, 0.0)):
        """
        Generates entire set of graphical reports for the megastructure design.
        :param output_folder: Output folder to save all images to.
        :param draw_individual_slat_reports: If set, to true, will generate individual slat reports (slow).
        :param generate_3d_video: If set to true, will generate a 3D video of the design.
        :param colormap: Colormap to extract layer colors from
        :param cargo_colormap: Colormap to extract cargo colors from
        :param seed_color: Color of the seed in the design.
        :return: N/A
        """
        print(Fore.CYAN + 'Generating graphical reports for megastructure design, this might take a few seconds...')
        create_dir_if_empty(output_folder)
        self.create_graphical_slat_view(save_to_folder=output_folder, instant_view=False, colormap=colormap,
                                        cargo_colormap=cargo_colormap, seed_color=seed_color)
        self.create_graphical_assembly_handle_view(save_to_folder=output_folder, instant_view=False, colormap=colormap)
        if draw_individual_slat_reports:
            self.create_graphical_slat_views(output_folder, colormap=colormap)
        if generate_3d_video:
            self.create_graphical_3D_view(output_folder, colormap=colormap, cargo_colormap=cargo_colormap,
                                          seed_color=seed_color)

    def export_design(self, filename, folder):
        """
        Exports the entire design to a single excel file.
        All individual slat, cargo, handle and seed arrays are exported into separate sheets.
        TODO: code doesn't feel optimal, could possibly be streamlined.
        :param filename: Output .xlsx filename
        :param folder: Output folder
        :return: N/A
        """

        writer = pd.ExcelWriter(os.path.join(folder, filename), engine='xlsxwriter')
        excel_conditional_formatting = {'type': '3_color_scale',
                                        'criteria': '<>',
                                        'min_color': "#63BE7B",  # Green
                                        'mid_color': "#FFEB84",  # Yellow
                                        'max_color': "#F8696B",  # Red
                                        'value': 0}

        # prints out slat dataframes
        for layer_index in range(self.slat_array.shape[-1]):
            df = pd.DataFrame(self.slat_array[..., layer_index])
            df.to_excel(writer, sheet_name=f'slat_layer_{layer_index + 1}', index=False, header=False)

            # Apply conditional formatting for easy color-based identification
            writer.sheets[f'slat_layer_{layer_index + 1}'].conditional_format(0, 0, df.shape[0], df.shape[1] - 1,
                                                                              excel_conditional_formatting)

        # prints out handle dataframes
        for layer_index in range(self.handle_arrays.shape[-1]):
            df = pd.DataFrame(self.handle_arrays[..., layer_index])
            df.to_excel(writer, sheet_name=f'handle_interface_{layer_index + 1}', index=False, header=False)
            # Apply conditional formatting
            writer.sheets[f'handle_interface_{layer_index + 1}'].conditional_format(0, 0, df.shape[0], df.shape[1] - 1,
                                                                                    excel_conditional_formatting)

        # prepares and sorts cargo dataframes
        cargo_dfs = []
        for c_layer in range((self.slat_array.shape[-1] * 2)):
            cargo_dfs.append(pd.DataFrame(np.zeros(shape=(self.slat_array.shape[0], self.slat_array.shape[1]))))

        # prepares a list of orientations to make it easier to distinguish between all the possible cargo locations
        orientation_list = ([self.layer_interface_orientations[0]] +
                            [item for sublist in self.layer_interface_orientations[1:-1] for item in sublist]
                            + [self.layer_interface_orientations[-1]])
        # traverses the cargo dict and assigns the cargo to different arrays based on layer and orientation
        for key, val in self.cargo_dict.items():
            (y, x), layer, orientation = key
            sel_layer_orientations = orientation_list[2 * layer - 2: 2 * layer]
            cargo_dfs[2 * layer - 2 + sel_layer_orientations.index(orientation)].iloc[y, x] = val

        # prints out cargo dataframes
        layer = 0
        for index, df in enumerate(cargo_dfs):
            if index % 2 == 0:
                position = 'lower'
                layer += 1
            else:
                position = 'upper'
            # nomenclature is 'layer ID-top/bottom-H2/H5'
            df.to_excel(writer, sheet_name=f'cargo_layer_{layer}_{position}_h{orientation_list[index]}', index=False,
                        header=False)
            writer.sheets[f'cargo_layer_{layer}_{position}_h{orientation_list[index]}'].conditional_format(0, 0, df.shape[0], df.shape[1] - 1, excel_conditional_formatting)

        # prints out single seed dataframe if available
        if self.seed_array is not None:
            df = pd.DataFrame(self.seed_array[1])
            df.to_excel(writer, sheet_name=f'seed_layer_{self.seed_array[0]}', index=False, header=False)
            writer.sheets[f'seed_layer_{self.seed_array[0]}'].conditional_format(0, 0,
                                                                                 df.shape[0],
                                                                                 df.shape[1] - 1,
                                                                                 excel_conditional_formatting)

        # prints out essential metadata required to regenerate design

        reversed_slats = []
        for slat in self.slats.values():
            if slat.reversed_slat:
                reversed_slats.append(slat.ID)
        metadata = pd.DataFrame.from_dict({'Layer Interface Orientations': [self.layer_interface_orientations],
                                           'Connection Angle': [self.connection_angle],
                                           'Reversed Slats': [reversed_slats]},
                                          orient='index')

        metadata.to_excel(writer, sheet_name='metadata', header=False)

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
            if 'slat' in key:
                layer_count += 1

        # preparing and reading in slat/handle arrays
        slat_array = np.zeros((design_df['slat_layer_1'].shape[0], design_df['slat_layer_1'].shape[1], layer_count))
        handle_array = np.zeros(
            (design_df['slat_layer_1'].shape[0], design_df['slat_layer_1'].shape[1], layer_count - 1))
        for i in range(layer_count):
            slat_array[..., i] = design_df['slat_layer_%s' % (i + 1)].values
            if i != layer_count - 1:
                handle_array[..., i] = design_df['handle_interface_%s' % (i + 1)].values

        # reading in cargo arrays and transferring to a dictionary
        cargo_dict = {}
        seed_array = None
        for i, key in enumerate(design_df.keys()):
            if 'cargo' in key:
                layer = int(key.split('_')[2])
                orientation = int(key.split('_')[4][-1])
                cargo_array = design_df[key].values
                cargo_coords = np.where(
                    cargo_array != 0)  # only extracts a value if there is cargo present, reducing clutter
                for y, x in zip(cargo_coords[0], cargo_coords[1]):
                    cargo_dict[((y, x), layer, orientation)] = cargo_array[y, x]
            if 'seed' in key:
                layer = int(key.split('_')[-1])
                seed_array = (layer, design_df[key].values)

        # extracts and formats metadata
        metadata = design_df['metadata']
        metadata.set_index(metadata.columns[0], inplace=True)
        layer_interface_orientations = ast.literal_eval(metadata.loc['Layer Interface Orientations'].iloc[0])
        connection_angle = metadata.loc['Connection Angle'].iloc[0]
        reversed_slats = ast.literal_eval(metadata.loc['Reversed Slats'].iloc[0])

        return slat_array, handle_array, seed_array, cargo_dict, layer_interface_orientations, connection_angle, reversed_slats
