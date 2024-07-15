from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt
from colorama import Fore
import os
import matplotlib as mpl

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

    def __init__(self, slat_array, layer_interface_orientations=None, connection_angle='90'):
        """
        :param slat_array: Array of slat positions (3D - X,Y, layer ID) containing the positions of all slats in the design.
        :param layer_interface_orientations: The direction each slat will be facing in the design.
        :param connection_angle: The angle at which the slats will be connected.  For now, only 90 and 60 grids are supported.
        E.g. for a 2 layer design, [2, 5, 2] implies that the bottom layer will have H2 handles sticking out,
        the connecting interface will have H5 handles and the top layer will have H2 handles again.
        TODO: how to enforce slat length?  Will this need to change in the future?
        TODO: how do we consider the additional 12nm/6nm on either end of the slat?
        """
        self.slat_array = slat_array
        self.handle_arrays = None
        self.seed_array = None
        self.cargo_arrays = []
        self.slats = {}
        self.num_layers = slat_array.shape[2]
        self.connection_angle = connection_angle

        if connection_angle not in ['60', '90']:
            raise NotImplementedError('Only 90 and 60 degree connection angles are supported.')

        self.grid_xd = connection_angles[connection_angle][0]
        self.grid_yd = connection_angles[connection_angle][1]

        # if no custom interface supplied, assuming alternating H2/H5 handles,
        # with H2 at the bottom, H5 at the top, and alternating connections in between
        # e.g. for a 3-layer structure, layer_interface_orientations = [2, (5, 2), (5,2), 5]
        if not layer_interface_orientations:
            self.layer_interface_orientations = [2] + [(5, 2)] * (self.num_layers - 1) + [5]
        else:
            self.layer_interface_orientations = layer_interface_orientations

        self.slats = convert_slat_array_into_slat_objects(slat_array)

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
                slat_crisscross_interfaces.extend([self.layer_interface_orientations[slat.layer - 1][1],
                                                   self.layer_interface_orientations[slat.layer][0]])
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
                                                                         handle_val),
                                               descriptor='Ass. Handle %s, Plate %s' % (handle_val, sel_plates.get_plate_name(slat_position_index + 1, slat_side, handle_val)))

    def assign_seed_handles(self, seed_array, seed_plate, layer_id=1):
        """
        Assigns seed handles to the slats based on the seed array provided.
        :param seed_array: 2D array with positioning of seed.  Each row of the seed should have a unique ID.
        :param seed_plate: Plate class with sequences to draw from.
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
            seed_value = seed_array[y, x]

            if layer_id == 1:
                bottom_slat_side = self.layer_interface_orientations[0]
            else:
                bottom_slat_side = self.layer_interface_orientations[layer_id - 1][1]

            if bottom_slat_side == 5:
                raise NotImplementedError('Seed placement on H5 side not yet supported.')

            if not isinstance(seed_plate.get_sequence(slat_position, 2, seed_value), str):
                raise RuntimeError('Seed plate selected cannot support placement on canvas.')

            selected_slat.set_handle(slat_position, bottom_slat_side,
                                     seed_plate.get_sequence(slat_position, 2, seed_value),
                                     seed_plate.get_well(slat_position, 2, seed_value),
                                     seed_plate.get_plate_name(),
                                     descriptor='Seed Handle, Plate %s' % seed_plate.get_plate_name())

        if len(seed_coords[0]) == 0:
            print((Fore.RED + 'WARNING: No seed handles were set - is your seed pattern array correct?'))

        self.seed_array = (layer_id, seed_array)

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
            slat_ID = self.slat_array[y, x, sel_layer - 1]
            if slat_ID == 0:
                raise RuntimeError('There is a cargo coordinate placed on a non-slat position.  '
                                   'Please re-verify your cargo pattern array.')
            selected_slat = self.slats[get_slat_key(sel_layer, slat_ID)]
            slat_position = selected_slat.slat_coordinate_to_position[(y, x)]
            cargo_value = cargo_array[y, x]

            if not isinstance(cargo_plate.get_sequence(slat_position, handle_orientation, cargo_value), str):
                raise RuntimeError('Cargo plate selected cannot support placement on canvas.')

            selected_slat.set_handle(slat_position, handle_orientation,
                                     cargo_plate.get_sequence(slat_position, handle_orientation, cargo_value),
                                     cargo_plate.get_well(slat_position, handle_orientation, cargo_value),
                                     cargo_plate.get_plate_name(),
                                     descriptor='Cargo Plate %s, Handle %s' % (cargo_plate.get_plate_name(), cargo_value))

        self.cargo_arrays.append((sel_layer, handle_orientation, cargo_array))

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
        while slat_count < len(self.slats):  # will loop through the design until all slats have been given a home
            if slat_count == 0:  # first extracts slats that will attach to the seed
                first_step_slats = set()
                seed_coords = np.where(self.seed_array[1] > 0)
                for y, x in zip(seed_coords[0], seed_coords[1]):  # extracts the slat ids from the layer connecting to the seed
                    overlapping_slat = (self.seed_array[0], self.slat_array[y, x, self.seed_array[0]-1])
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
                        slat_posns = np.where(self.slat_array[..., layer-1] == slat)
                        for y, x in zip(slat_posns[0], slat_posns[1]):
                            if layer != 1 and self.slat_array[y, x, layer-2] != 0:  # checks the layer below
                                slat_overlap_counts[(layer-1, self.slat_array[y, x, layer-2])] += 1
                            if layer != self.num_layers and self.slat_array[y, x, layer] != 0:  # checks the layer above
                                slat_overlap_counts[(layer+1, self.slat_array[y, x, layer])] += 1
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

        return slat_id_animation_classification

    def create_graphical_slat_view(self, save_to_folder=None, instant_view=True,
                                   include_cargo=True, include_seed=True,
                                   colormap='Set1', cargo_colormap='Set1'):
        """
        Creates a graphical view of the slats, cargo and seeds in the design.  Refer to the graphics module for more details.
        :param save_to_folder: Set to the filepath of a folder where all figures will be saved.
        :param instant_view: Set to True to plot the figures immediately to your active view.
        :param include_cargo: Set to True to include cargo in the graphical view.
        :param include_seed: Set to True to include the seed in the graphical view.
        :param colormap: The colormap to sample from for each additional layer.
        :param cargo_colormap: The colormap to sample from for each cargo type.
        :return: N/A
        """

        create_graphical_slat_view(self.slat_array,
                                   layer_interface_orientations=self.layer_interface_orientations,
                                   slats=self.slats, seed_array=self.seed_array if include_seed else None,
                                   cargo_arrays=self.cargo_arrays if include_cargo else None,
                                   save_to_folder=save_to_folder, instant_view=instant_view,
                                   connection_angle=self.connection_angle,
                                   colormap=colormap,
                                   cargo_colormap=cargo_colormap)

    def create_graphical_assembly_handle_view(self, save_to_folder=None, instant_view=True, colormap='Set1'):
        """
        Creates a graphical view of the assembly handles in the design.  Refer to the graphics module for more details.
        :param save_to_folder: Set to the filepath of a folder where all figures will be saved.
        :param instant_view: Set to True to plot the figures immediately to your active view.
        :param colormap: The colormap to sample from for each additional layer.
        :return: N/A
        """

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
                h2_handle = slat.H2_handles[i+1]
                h5_handle = slat.H5_handles[i+1]

                plt.text(i, 3.5, h2_handle['descriptor'], color='black', zorder=3, ha='center',
                         fontsize=15, weight='bold', rotation='vertical')
                plt.text(i, 0.5, h5_handle['descriptor'], color='black', zorder=3, ha='center',
                         va='top', fontsize=15, weight='bold', rotation='vertical')

                plt.plot([i, i], [2, 3], color='black', linewidth=12, zorder=1)
                plt.plot([i, i], [2, 1], color='black', linewidth=12, zorder=1)

            plt.tight_layout()
            plt.savefig(os.path.join(output_folder, '%s.png' % slat_id), dpi=300)
            plt.close(l_fig)

    def create_graphical_3D_view(self, save_folder, window_size=(2048, 2048), colormap='Set1'):
        """
        Creates a 3D video of the megastructure slat design.
        :param save_folder: Folder to save all video to.
        :param window_size: Resolution of video generated.  2048x2048 seems reasonable in most cases.
        :param colormap: Colormap to extract layer colors from
        :return: N/A
        """
        create_graphical_3D_view(self.slat_array, save_folder, slats=self.slats, connection_angle=self.connection_angle,
                                 window_size=window_size, colormap=colormap)

    def create_blender_3D_view(self, save_folder, animate_assembly=False,
                               custom_assembly_groups=None, colormap='Set1'):
        """
        Creates a 3D model of the megastructure slat design as a Blender file.
        :param save_folder: Folder to save all video to.
        :param animate_assembly: Set to true to also generate an animation of the design being assembled group by group
        :param custom_assembly_groups: If set, will use the specific provided dictionary to assign slats to the animation order.
        :param colormap: Colormap to extract layer colors from
        :return: N/A
        """
        if animate_assembly:
            if custom_assembly_groups:
                assembly_groups = custom_assembly_groups
            else:
                assembly_groups = self.get_slats_by_assembly_stage()
        else:
            assembly_groups = None

        create_graphical_3D_view_bpy(self.slat_array, save_folder, slats=self.slats,
                                     animate_slat_group_dict=assembly_groups,
                                     connection_angle=self.connection_angle,
                                     colormap=colormap)

    def create_standard_graphical_report(self, output_folder, draw_individual_slat_reports=False,
                                         colormap='Dark2', cargo_colormap='Set1'):
        """
        Generates entire set of graphical reports for the megastructure design.
        :param output_folder: Output folder to save all images to.
        :param draw_individual_slat_reports: If set, to true, will generate individual slat reports (slow).
        :param colormap: Colormap to extract layer colors from
        :param cargo_colormap: Colormap to extract cargo colors from
        :return: N/A
        """
        print(Fore.CYAN + 'Generating graphical reports for megastructure design, this might take a few seconds...')
        create_dir_if_empty(output_folder)
        self.create_graphical_slat_view(save_to_folder=output_folder, instant_view=False, colormap=colormap,
                                        cargo_colormap=cargo_colormap)
        self.create_graphical_assembly_handle_view(save_to_folder=output_folder, instant_view=False, colormap=colormap)
        if draw_individual_slat_reports:
            self.create_graphical_slat_views(output_folder, colormap=colormap)
        self.create_graphical_3D_view(output_folder, colormap=colormap)


