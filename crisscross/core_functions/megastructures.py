import math
import numpy as np
import matplotlib.pyplot as plt
from colorama import Fore
import os
import matplotlib as mpl
import importlib

from crisscross.core_functions.slats import Slat
from crisscross.helper_functions import create_dir_if_empty

pyvista_spec = importlib.util.find_spec("pyvista")  # only imports pyvista if this is available
if pyvista_spec is not None:
    import pyvista as pv
else:
    print('Pyvista not installed.  3D graphical views cannot be created.')

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
        if connection_angle == '90':
            self.grid_xd = 1
            self.grid_yd = 1
        elif connection_angle == '60':
            self.grid_yd = 1/2
            self.grid_xd = np.sqrt((1**2) - (self.grid_yd**2))
        else:
            raise NotImplementedError('Only 90 and 60 degree connection angles are supported.')

        # if no custom interface supplied, assuming alternating H2/H5 handles,
        # with H2 at the bottom, H5 at the top, and alternating connections in between
        # e.g. for a 3-layer structure, layer_interface_orientations = [2, (5, 2), (5,2), 5]
        if not layer_interface_orientations:
            self.layer_interface_orientations = [2] + [(5, 2)] * (self.num_layers - 1) + [5]
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

            selected_slat = self.slats[self.get_slat_key(layer_id, slat_ID)]
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
            selected_slat = self.slats[self.get_slat_key(sel_layer, slat_ID)]
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

    def slat_axes_setup(self, axis, reverse_y=False):
        if reverse_y:
            axis.set_ylim(-0.5*self.grid_yd, (self.slat_array.shape[0] + 0.5)*self.grid_yd)
        else:
            axis.set_ylim((self.slat_array.shape[0] + 0.5)*self.grid_yd, -0.5*self.grid_yd)
        axis.set_xlim(-0.5*self.grid_xd, (self.slat_array.shape[1] + 0.5)*self.grid_xd)
        axis.axis('scaled')
        axis.axis('off')

    def point_converter(self, point):
        return point[0] * self.grid_yd, point[1] * self.grid_xd

    def create_graphical_slat_view(self, save_to_folder=None, instant_view=True,
                                   include_cargo=True, include_seed=True,
                                   slat_width=4, colormap='Set1', cargo_colormap='Set1'):
        """
        Creates a graphical view of all slats in the assembled design, including cargo and seed handles.
        A single figure is created for the global view of the structure, as well as individual figures
        for each layer in the design.
        :param save_to_folder: Set to the filepath of a folder where all figures will be saved.
        :param instant_view: Set to True to plot the figures immediately to your active view.
        :param include_cargo: Will print out cargo handle positions by default.  Turn this off here.
        :param include_seed: Will print out seed handle positions by default.  Turn this off here.
        :param slat_width: The width to use for the slat lines.
        :param colormap: The colormap to sample from for each additional layer.
        :param cargo_colormap: The colormap to sample from for each cargo type.
        :return: N/A
        """

        global_fig, global_ax = plt.subplots(1, 2, figsize=(20, 12))
        global_fig.suptitle('Global View', fontsize=35)
        self.slat_axes_setup(global_ax[0])
        self.slat_axes_setup(global_ax[1])
        global_ax[0].set_title('Top View', fontsize=35)
        global_ax[1].set_title('Bottom View', fontsize=35)

        layer_figures = []
        for l_ind, layer in enumerate(range(self.num_layers)):
            l_fig, l_ax = plt.subplots(1, 2, figsize=(20, 12))
            self.slat_axes_setup(l_ax[0])
            self.slat_axes_setup(l_ax[1])
            l_ax[0].set_title('Top View', fontsize=35)
            l_ax[1].set_title('Bottom View', fontsize=35)
            l_fig.suptitle('Layer %s' % (l_ind + 1), fontsize=35)
            layer_figures.append((l_fig, l_ax))

        for slat_id, slat in self.slats.items():

            if len(slat.slat_coordinate_to_position) == 0:
                print(Fore.YELLOW + 'WARNING: Slat %s was ignored from graphical '
                                    'view as it does not have a grid position defined.' % slat_id)
                continue
            start_pos = slat.slat_position_to_coordinate[1]
            end_pos = slat.slat_position_to_coordinate[slat.max_length]

            start_pos = self.point_converter(start_pos)  # this is necessary to ensure scaling is correct for 60deg angle slats
            end_pos = self.point_converter(end_pos)

            layer_color = mpl.colormaps[colormap].colors[slat.layer - 1]
            layer_figures[slat.layer - 1][1][0].plot([start_pos[1], end_pos[1]], [start_pos[0], end_pos[0]],
                                                     color=layer_color, linewidth=slat_width, zorder=1)
            layer_figures[slat.layer - 1][1][1].plot([start_pos[1], end_pos[1]], [start_pos[0], end_pos[0]],
                                                     color=layer_color, linewidth=slat_width, zorder=1)

            global_ax[0].plot([start_pos[1], end_pos[1]], [start_pos[0], end_pos[0]],
                              color=layer_color, linewidth=slat_width, alpha=0.5, zorder=slat.layer)
            global_ax[1].plot([start_pos[1], end_pos[1]], [start_pos[0], end_pos[0]],
                              color=layer_color, linewidth=slat_width, alpha=0.5, zorder=self.num_layers - slat.layer)

        if include_seed and self.seed_array:
            # TODO: IF WE ATTACH THE SEED TO THE TOP SIDE OF A LAYER, THEN THE LOGIC HERE NEEDS TO BE ADJUSTED
            seed_layer = self.seed_array[0]
            seed_plot_points = np.where(self.seed_array[1] > 0)
            transformed_spp = [seed_plot_points[0] * self.grid_yd,  seed_plot_points[1] * self.grid_xd]
            layer_figures[seed_layer - 1][1][1].scatter(transformed_spp[1], transformed_spp[0], color='black', s=100,
                                                        zorder=10)
            global_ax[0].scatter(transformed_spp[1], transformed_spp[0], color='black', s=100, alpha=0.5,
                                 zorder=seed_layer)
            global_ax[1].scatter(transformed_spp[1], transformed_spp[0], color='black', s=100, alpha=0.5,
                                 zorder=self.num_layers - seed_layer)

        if include_cargo and len(self.cargo_arrays) > 0:
            # TODO: is it worth setting a different colour for each different cargo here?
            # TODO: Is there some way to print the slat ID too?
            # TODO: will need to improve colour assignment process to include non-integers..
            for cargo_layer, cargo_orientation, cargo_array in self.cargo_arrays:
                cargo_plot_points = np.where(cargo_array > 0)
                # sets colour of annotation according to the cargo being added
                cargo_color_values = cargo_array[cargo_plot_points]
                cargo_color_values_rgb = []
                for col_id in cargo_color_values:
                    cargo_color_values_rgb.append(mpl.colormaps[cargo_colormap].colors[int(col_id)])

                transformed_cpp = [cargo_plot_points[0] * self.grid_yd, cargo_plot_points[1] * self.grid_xd]
                top_layer_side = self.layer_interface_orientations[cargo_layer]
                if isinstance(top_layer_side, tuple):
                    top_layer_side = top_layer_side[0]
                if top_layer_side == cargo_orientation:
                    top_or_bottom = 0
                else:
                    top_or_bottom = 1
                layer_figures[cargo_layer - 1][1][top_or_bottom].scatter(transformed_cpp[1], transformed_cpp[0],
                                                                         color=cargo_color_values_rgb, marker='s',
                                                                         s=100, zorder=10)
                global_ax[0].scatter(transformed_cpp[1], transformed_cpp[0], color=cargo_color_values_rgb, s=100,
                                     marker='s', alpha=0.5, zorder=cargo_layer)
                global_ax[1].scatter(transformed_cpp[1], transformed_cpp[0], color=cargo_color_values_rgb,
                                     s=100, marker='s', alpha=0.5, zorder=self.num_layers - cargo_layer)

        global_fig.tight_layout()
        if instant_view:
            global_fig.show()
        if save_to_folder:
            global_fig.savefig(os.path.join(save_to_folder, 'global_view.png'), dpi=300)

        for fig_ind, (fig, ax) in enumerate(layer_figures):
            fig.tight_layout()
            if instant_view:
                fig.show()
            if save_to_folder:
                fig.savefig(os.path.join(save_to_folder, 'layer_%s.png' % (fig_ind + 1)), dpi=300)
            plt.close(fig)

    def create_graphical_assembly_handle_view(self, save_to_folder=None, instant_view=True,
                                              slat_width=4, colormap='Set1'):
        """
        Creates a graphical view of all handles in the assembled design, along with a side profile.
        :param save_to_folder: Set to the filepath of a folder where all figures will be saved.
        :param instant_view: Set to True to plot the figures immediately to your active view.
        :param slat_width: The width to use for the slat lines.
        :param colormap: The colormap to sample from for each additional layer.
        :return:
        """

        # Figure Prep
        interface_figures = []
        for l_ind, layer in enumerate(range(self.num_layers - 1)):
            l_fig, l_ax = plt.subplots(1, 2, figsize=(20, 12))
            self.slat_axes_setup(l_ax[0])
            self.slat_axes_setup(l_ax[1], reverse_y=True)
            l_ax[0].set_title('Handle View', fontsize=35)
            l_ax[1].set_title('Side View', fontsize=35)
            l_fig.suptitle('Handles Between Layer %s and %s' % (l_ind + 1, l_ind + 2), fontsize=35)
            interface_figures.append((l_fig, l_ax))

        # Painting in slats
        for slat_id, slat in self.slats.items():
            if len(slat.slat_coordinate_to_position) == 0:
                print(Fore.YELLOW + 'WARNING: Slat %s was ignored from graphical '
                                    'view as it does not have a grid position defined.' % slat_id)
                continue
            start_pos = slat.slat_position_to_coordinate[1]
            end_pos = slat.slat_position_to_coordinate[slat.max_length]
            start_pos = self.point_converter(start_pos)  # this is necessary to ensure scaling is correct for 60deg angle slats
            end_pos = self.point_converter(end_pos)

            layer_color = mpl.colormaps[colormap].colors[slat.layer - 1]

            if slat.layer == 1:
                plot_positions = [0]
            elif slat.layer == self.num_layers:
                plot_positions = [self.num_layers - 2]
            else:
                plot_positions = [slat.layer - 1, slat.layer - 2]

            for p in plot_positions:
                interface_figures[p][1][0].plot([start_pos[1], end_pos[1]], [start_pos[0], end_pos[0]],
                                                color=layer_color, linewidth=slat_width, zorder=1, alpha=0.3)

        # Painting in handles
        for handle_layer_num in range(self.handle_arrays.shape[2]):
            for i in range(self.handle_arrays.shape[0]):
                for j in range(self.handle_arrays.shape[1]):
                    val = self.handle_arrays[i, j, handle_layer_num]
                    x_pos = j * self.grid_xd  # this is necessary to ensure scaling is correct for 60deg angle slats
                    y_pos = i * self.grid_yd
                    if val > 0:
                        interface_figures[handle_layer_num][1][0].text(x_pos, y_pos, int(val), ha='center', va='center',
                                                                       color='black', zorder=3, fontsize=8)

        # Preparing layer lines for side profile
        layer_lines = []
        layer_v_jump = 0.1  # set a 10% full-height jump between layers for aesthetic reasons
        midway_v_point = ((self.slat_array.shape[0] + 1)/2)*self.grid_yd
        full_v_scale = (self.slat_array.shape[0] + 1)*self.grid_yd
        full_x_scale = (self.slat_array.shape[1] + 1)*self.grid_xd

        if self.num_layers % 2 == 0:  # even and odd num of layers should have different spacing to remain centred
            start_point = midway_v_point - (layer_v_jump/2) - (layer_v_jump * ((self.num_layers/2)-1) * full_v_scale)
        else:
            start_point = midway_v_point - (layer_v_jump * (math.floor(self.num_layers/2)) * full_v_scale)

        for layer in range(self.num_layers):  # prepares actual lines here
            layer_lines.append([[-0.5*self.grid_xd, (self.slat_array.shape[1] + 0.5)*self.grid_xd],
                                [start_point + (layer_v_jump*layer*full_v_scale),
                                 start_point + (layer_v_jump*layer*full_v_scale)]])

        # layer lines are painted here, along with arrows and annotations
        annotation_vert_offset = 0.02
        annotation_vert_offset_btm = 0.026  # made a second offset scale here due to the way the font is positioned in the figure
        annotation_x_position = full_x_scale/2
        for fig_ind, (fig, ax) in enumerate(interface_figures):
            for l_ind, line in enumerate(layer_lines):
                ax[1].plot(line[0], line[1], color=mpl.colormaps[colormap].colors[l_ind], linewidth=slat_width)

                # extracts interface numbers from megastructure data
                if l_ind == 0:
                    bottom_interface = self.layer_interface_orientations[0]
                    top_interface = self.layer_interface_orientations[1][0]
                elif l_ind == self.num_layers - 1:
                    bottom_interface = self.layer_interface_orientations[-2][1]
                    top_interface = self.layer_interface_orientations[-1]
                else:
                    bottom_interface = self.layer_interface_orientations[l_ind][1]
                    top_interface = self.layer_interface_orientations[l_ind + 1][0]

                ax[1].text(annotation_x_position, line[1][1] - (annotation_vert_offset_btm * full_v_scale),
                           'H%s' % bottom_interface, ha='center', va='center', color='black', zorder=3, fontsize=25, weight='bold')
                ax[1].text(annotation_x_position, line[1][1] + (annotation_vert_offset * full_v_scale),
                           'H%s' % top_interface, ha='center', va='center', color='black', zorder=3, fontsize=25, weight='bold')

            y_arrow_pos = layer_lines[fig_ind+1][1][1] - (layer_lines[fig_ind+1][1][1] - layer_lines[fig_ind][1][1])/2
            x_arrow_1 = -0.5*self.grid_xd
            x_arrow_2 = (self.slat_array.shape[1] + 0.5)*self.grid_xd
            ax[1].arrow(x_arrow_1, y_arrow_pos, 0.1 * full_x_scale, 0, width=(0.8 * full_v_scale/67), fc='k', ec='k') # arrow width was calibrated on a canvas with a vertical size of 67
            ax[1].arrow(x_arrow_2, y_arrow_pos, -0.1 * full_x_scale, 0, width=(0.8 * full_v_scale/67), fc='k', ec='k')

        # final display and saving
        for fig_ind, (fig, ax) in enumerate(interface_figures):
            fig.tight_layout()
            if instant_view:
                fig.show()
            if save_to_folder:
                fig.savefig(os.path.join(save_to_folder,
                                         'handles_layer_%s_%s.png' % (fig_ind + 1, fig_ind + 2)), dpi=300)
            plt.close(fig)

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
        Creates a 3D video of the megastructure slat design. TODO: add cargo and seeds to this view too.
        :param save_folder: Folder to save all video to.
        :param window_size: Resolution of video generated.  2048x2048 seems reasonable in most cases.
        :param colormap: Colormap to extract layer colors from
        :return: N/A
        """

        plotter = pv.Plotter(window_size=window_size, off_screen=True)

        for slat_id, slat in self.slats.items(): # Z-height is set to 1 here, could be interested in changing in some cases
            if len(slat.slat_position_to_coordinate) == 0:
                print(Fore.YELLOW + 'WARNING: Slat %s was ignored from 3D graphical '
                                    'view as it does not have a grid position defined.' % slat_id)
                continue

            pos1 = slat.slat_position_to_coordinate[1]
            pos2 = slat.slat_position_to_coordinate[32]

            layer = slat.layer
            length = slat.max_length
            layer_color = mpl.colormaps[colormap].colors[slat.layer - 1]

            # TODO: can we represent the cylinders with the precise dimensions of the real thing i.e. with the 12/6nm extension on either end?
            start_point = (pos1[1] * self.grid_xd, pos1[0] * self.grid_yd, layer - 1)
            end_point = (pos2[1] * self.grid_xd, pos2[0] * self.grid_yd, layer - 1)

            # Calculate the center and direction from start and end points
            center = ((start_point[0] + end_point[0]) / 2, (start_point[1] + end_point[1]) / 2, layer - 1)
            direction = (end_point[0] - start_point[0], end_point[1] - start_point[1], end_point[2] - start_point[2])

            # Create the cylinder
            cylinder = pv.Cylinder(center=center, direction=direction, radius=0.5, height=length)
            plotter.add_mesh(cylinder, color=layer_color)

        plotter.add_axes(interactive=True)

        # Open a movie file
        plotter.open_movie(os.path.join(save_folder, '3D_design_view.mp4'))
        plotter.show(auto_close=False)

        # Again, it might be of interest to adjust parameters here for different designs
        path = plotter.generate_orbital_path(n_points=200, shift=0.2, viewup=[0, 1, 0], factor=2.0)
        plotter.orbit_on_path(path, write_frames=True, viewup=[0, 1, 0], step=0.05)
        plotter.close()

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


