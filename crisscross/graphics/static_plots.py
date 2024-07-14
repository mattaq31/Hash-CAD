import os
import matplotlib.pyplot as plt
from colorama import Fore
import matplotlib as mpl
import numpy as np
import math

from crisscross.core_functions.slats import convert_slat_array_into_slat_objects
from crisscross.helper_functions.slat_salient_quantities import connection_angles


def slat_axes_setup(slat_array, axis, grid_xd, grid_yd, reverse_y=False):
    if reverse_y:
        axis.set_ylim(-0.5 * grid_yd, (slat_array.shape[0] + 0.5) * grid_yd)
    else:
        axis.set_ylim((slat_array.shape[0] + 0.5) * grid_yd, -0.5 * grid_yd)
    axis.set_xlim(-0.5 * grid_xd, (slat_array.shape[1] + 0.5) * grid_xd)
    axis.axis('scaled')
    axis.axis('off')


def physical_point_scale_convert(point, grid_xd, grid_yd):
    return point[0] * grid_yd, point[1] * grid_xd


def create_graphical_slat_view(slat_array,  layer_interface_orientations=None,
                               slats=None, seed_array=None,
                               cargo_arrays=None, save_to_folder=None, instant_view=True,
                               slat_width=4, connection_angle='90',
                               colormap='Set1',
                               cargo_colormap='Set1'):
    """
    Creates a graphical view of all slats in the assembled design, including cargo and seed handles.
    A single figure is created for the global view of the structure, as well as individual figures
    for each layer in the design.
    :param slat_array: A 3D numpy array with x/y slat positions (slat ID placed in each position occupied)
    :param layer_interface_orientations: A list of tuples (or integers for top/bottom), each containing the bottom and top interface numbers for each layer
    :param slats: Dictionary of slat objects (if not provided, will be generated from slat_array)
    :param seed_array: A tuple of (layer_position, 2D numpy array with the seed handle positions)
    :param cargo_arrays: A list of tuples, each containing the layer position, orientation, and 2D numpy array with cargo handle positions
    :param save_to_folder: Set to the filepath of a folder where all figures will be saved.
    :param instant_view: Set to True to plot the figures immediately to your active view.
    :param slat_width: The width to use for the slat lines.
    :param connection_angle: The angle of the slats in the design (either '90' or '60' for now).
    :param colormap: The colormap to sample from for each additional layer.
    :param cargo_colormap: The colormap to sample from for each cargo type.
    :return: N/A
    """

    num_layers = slat_array.shape[2]
    if slats is None:
        slats = convert_slat_array_into_slat_objects(slat_array)
    if not isinstance(cargo_arrays, list) and cargo_arrays is not None:
        cargo_arrays = [cargo_arrays]
    if layer_interface_orientations is None:
        layer_interface_orientations = [2] + [(5, 2)] * (num_layers - 1) + [5]

    grid_xd, grid_yd = connection_angles[connection_angle][0], connection_angles[connection_angle][1]

    global_fig, global_ax = plt.subplots(1, 2, figsize=(20, 12))
    global_fig.suptitle('Global View', fontsize=35)
    slat_axes_setup(slat_array, global_ax[0], grid_xd, grid_yd)
    slat_axes_setup(slat_array, global_ax[1], grid_xd, grid_yd)
    global_ax[0].set_title('Top View', fontsize=35)
    global_ax[1].set_title('Bottom View', fontsize=35)

    layer_figures = []
    for l_ind, layer in enumerate(range(num_layers)):
        l_fig, l_ax = plt.subplots(1, 2, figsize=(20, 12))
        slat_axes_setup(slat_array, l_ax[0], grid_xd, grid_yd)
        slat_axes_setup(slat_array, l_ax[1], grid_xd, grid_yd)
        l_ax[0].set_title('Top View', fontsize=35)
        l_ax[1].set_title('Bottom View', fontsize=35)
        l_fig.suptitle('Layer %s' % (l_ind + 1), fontsize=35)
        layer_figures.append((l_fig, l_ax))

    for slat_id, slat in slats.items():

        if len(slat.slat_coordinate_to_position) == 0:
            print(Fore.YELLOW + 'WARNING: Slat %s was ignored from graphical '
                                'view as it does not have a grid position defined.' % slat_id)
            continue
        start_pos = slat.slat_position_to_coordinate[1]
        end_pos = slat.slat_position_to_coordinate[slat.max_length]

        start_pos = physical_point_scale_convert(start_pos, grid_xd, grid_yd)  # this is necessary to ensure scaling is correct for 60deg angle slats
        end_pos = physical_point_scale_convert(end_pos, grid_xd, grid_yd)

        layer_color = mpl.colormaps[colormap].colors[slat.layer - 1]
        layer_figures[slat.layer - 1][1][0].plot([start_pos[1], end_pos[1]], [start_pos[0], end_pos[0]],
                                                 color=layer_color, linewidth=slat_width, zorder=1)
        layer_figures[slat.layer - 1][1][1].plot([start_pos[1], end_pos[1]], [start_pos[0], end_pos[0]],
                                                 color=layer_color, linewidth=slat_width, zorder=1)

        global_ax[0].plot([start_pos[1], end_pos[1]], [start_pos[0], end_pos[0]],
                          color=layer_color, linewidth=slat_width, alpha=0.5, zorder=slat.layer)
        global_ax[1].plot([start_pos[1], end_pos[1]], [start_pos[0], end_pos[0]],
                          color=layer_color, linewidth=slat_width, alpha=0.5, zorder=num_layers - slat.layer)

    if seed_array is not None:
        # TODO: IF WE ATTACH THE SEED TO THE TOP SIDE OF A LAYER, THEN THE LOGIC HERE NEEDS TO BE ADJUSTED
        seed_layer = seed_array[0]
        seed_plot_points = np.where(seed_array[1] > 0)
        transformed_spp = [seed_plot_points[0] * grid_yd, seed_plot_points[1] * grid_xd]
        layer_figures[seed_layer - 1][1][1].scatter(transformed_spp[1], transformed_spp[0], color='black', s=100,
                                                    zorder=10)
        global_ax[0].scatter(transformed_spp[1], transformed_spp[0], color='black', s=100, alpha=0.5,
                             zorder=seed_layer)
        global_ax[1].scatter(transformed_spp[1], transformed_spp[0], color='black', s=100, alpha=0.5,
                             zorder=num_layers - seed_layer)

    if cargo_arrays is not None:
        # TODO: is it worth setting a different colour for each different cargo here?
        # TODO: Is there some way to print the slat ID too?
        # TODO: will need to improve colour assignment process to include non-integers..
        for cargo_layer, cargo_orientation, cargo_array in cargo_arrays:
            cargo_plot_points = np.where(cargo_array > 0)
            # sets colour of annotation according to the cargo being added
            cargo_color_values = cargo_array[cargo_plot_points]
            cargo_color_values_rgb = []
            for col_id in cargo_color_values:
                if int(col_id) >= len(mpl.colormaps[cargo_colormap].colors):
                    print(Fore.RED + 'WARNING: Cargo ID %s is out of range for the colormap. Recycling other colors for the higher IDs.' % col_id)
                    col_id = max(int(col_id) - len(mpl.colormaps[cargo_colormap].colors), 0)
                cargo_color_values_rgb.append(mpl.colormaps[cargo_colormap].colors[int(col_id)])

            transformed_cpp = [cargo_plot_points[0] * grid_yd, cargo_plot_points[1] * grid_xd]
            top_layer_side = layer_interface_orientations[cargo_layer]
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
                                 s=100, marker='s', alpha=0.5, zorder=num_layers - cargo_layer)

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


def create_graphical_assembly_handle_view(slat_array, handle_arrays, layer_interface_orientations=None,
                                          slats=None, save_to_folder=None, connection_angle='90',
                                          instant_view=True, slat_width=4, colormap='Set1'):
    """
    Creates a graphical view of all handles in the assembled design, along with a side profile.
    :param slat_array: A 3D numpy array with x/y slat positions (slat ID placed in each position occupied)
    :param handle_arrays: A 3D numpy array with x/y handle positions (handle ID placed in each position occupied)
    :param layer_interface_orientations: A list of tuples (or integers for top/bottom), each containing the bottom and top interface numbers for each layer
    :param slats: Dictionary of slat objects (if not provided, will be generated from slat_array)
    :param save_to_folder: Set to the filepath of a folder where all figures will be saved.
    :param connection_angle: The angle of the slats in the design (either '90' or '60' for now).
    :param instant_view: Set to True to plot the figures immediately to your active view.
    :param slat_width: The width to use for the slat lines.
    :param colormap: The colormap to sample from for each additional layer.
    :return: N/A
    """

    num_layers = slat_array.shape[2]
    if slats is None:
        slats = convert_slat_array_into_slat_objects(slat_array)

    if layer_interface_orientations is None:
        layer_interface_orientations = [2] + [(5, 2)] * (num_layers - 1) + [5]

    grid_xd, grid_yd = connection_angles[connection_angle][0], connection_angles[connection_angle][1]

    # Figure Prep
    interface_figures = []
    for l_ind, layer in enumerate(range(num_layers - 1)):
        l_fig, l_ax = plt.subplots(1, 2, figsize=(20, 12))
        slat_axes_setup(slat_array, l_ax[0], grid_xd, grid_yd)
        slat_axes_setup(slat_array, l_ax[1], grid_xd, grid_yd, reverse_y=True)
        l_ax[0].set_title('Handle View', fontsize=35)
        l_ax[1].set_title('Side View', fontsize=35)
        l_fig.suptitle('Handles Between Layer %s and %s' % (l_ind + 1, l_ind + 2), fontsize=35)
        interface_figures.append((l_fig, l_ax))

    # Painting in slats
    for slat_id, slat in slats.items():
        if len(slat.slat_coordinate_to_position) == 0:
            print(Fore.YELLOW + 'WARNING: Slat %s was ignored from graphical '
                                'view as it does not have a grid position defined.' % slat_id)
            continue
        start_pos = slat.slat_position_to_coordinate[1]
        end_pos = slat.slat_position_to_coordinate[slat.max_length]
        start_pos = physical_point_scale_convert(start_pos, grid_xd, grid_yd)  # this is necessary to ensure scaling is correct for 60deg angle slats
        end_pos = physical_point_scale_convert(end_pos, grid_xd, grid_yd)

        layer_color = mpl.colormaps[colormap].colors[slat.layer - 1]

        if slat.layer == 1:
            plot_positions = [0]
        elif slat.layer == num_layers:
            plot_positions = [num_layers - 2]
        else:
            plot_positions = [slat.layer - 1, slat.layer - 2]

        for p in plot_positions:
            interface_figures[p][1][0].plot([start_pos[1], end_pos[1]], [start_pos[0], end_pos[0]],
                                            color=layer_color, linewidth=slat_width, zorder=1, alpha=0.3)

    # Painting in handles
    for handle_layer_num in range(handle_arrays.shape[2]):
        for i in range(handle_arrays.shape[0]):
            for j in range(handle_arrays.shape[1]):
                val = handle_arrays[i, j, handle_layer_num]
                x_pos = j * grid_xd  # this is necessary to ensure scaling is correct for 60deg angle slats
                y_pos = i * grid_yd
                if val > 0:
                    interface_figures[handle_layer_num][1][0].text(x_pos, y_pos, int(val), ha='center', va='center',
                                                                   color='black', zorder=3, fontsize=8)

    # Preparing layer lines for side profile
    layer_lines = []
    layer_v_jump = 0.1  # set a 10% full-height jump between layers for aesthetic reasons
    midway_v_point = ((slat_array.shape[0] + 1)/2) * grid_yd
    full_v_scale = (slat_array.shape[0] + 1) * grid_yd
    full_x_scale = (slat_array.shape[1] + 1) * grid_xd

    if num_layers % 2 == 0:  # even and odd num of layers should have different spacing to remain centred
        start_point = midway_v_point - (layer_v_jump/2) - (layer_v_jump * ((num_layers/2)-1) * full_v_scale)
    else:
        start_point = midway_v_point - (layer_v_jump * (math.floor(num_layers/2)) * full_v_scale)

    for layer in range(num_layers):  # prepares actual lines here
        layer_lines.append([[-0.5*grid_xd, (slat_array.shape[1] + 0.5)*grid_xd],
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
                bottom_interface = layer_interface_orientations[0]
                top_interface = layer_interface_orientations[1][0]
            elif l_ind == num_layers - 1:
                bottom_interface = layer_interface_orientations[-2][1]
                top_interface = layer_interface_orientations[-1]
            else:
                bottom_interface = layer_interface_orientations[l_ind][1]
                top_interface = layer_interface_orientations[l_ind + 1][0]

            ax[1].text(annotation_x_position, line[1][1] - (annotation_vert_offset_btm * full_v_scale),
                       'H%s' % bottom_interface, ha='center', va='center', color='black', zorder=3, fontsize=25, weight='bold')
            ax[1].text(annotation_x_position, line[1][1] + (annotation_vert_offset * full_v_scale),
                       'H%s' % top_interface, ha='center', va='center', color='black', zorder=3, fontsize=25, weight='bold')

        y_arrow_pos = layer_lines[fig_ind+1][1][1] - (layer_lines[fig_ind+1][1][1] - layer_lines[fig_ind][1][1])/2
        x_arrow_1 = -0.5 * grid_xd
        x_arrow_2 = (slat_array.shape[1] + 0.5) * grid_xd
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
