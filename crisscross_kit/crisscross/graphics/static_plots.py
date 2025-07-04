import os
import textwrap

import matplotlib.pyplot as plt
from colorama import Fore
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


def cargo_legend_setup(*ax):
    for specific_axis in ax:
        handles, labels = specific_axis.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        if len(by_label) == 0:
            continue
        wrapped_labels = ["\n".join(textwrap.wrap(label, width=15)) for label in by_label.keys()]

        specific_axis.legend(by_label.values(), wrapped_labels, loc='upper center',
                             bbox_to_anchor=(0.5, 0.03),
                             ncol=3, fancybox=True, fontsize=16)


def create_graphical_slat_view(slat_array, layer_palette, cargo_palette=None, include_seed=True, include_cargo=True,
                               slats=None, save_to_folder=None, instant_view=True, filename_prepend='',
                               slat_width=4, connection_angle='90'):
    """
    Creates a graphical view of all slats in the assembled design, including cargo and seed handles.
    A single figure is created for the global view of the structure, as well as individual figures
    for each layer in the design.
    :param slat_array: A 3D numpy array with x/y slat positions (slat ID placed in each position occupied)
    :param layer_palette: Dictionary of layer information (e.g. top/bottom helix and colors), where keys are layer numbers.
    :param cargo_palette: Dictionary of cargo information (e.g. colors), where keys are cargo types.
    :param include_seed: Set to True to include seed handles in the graphical view.
    :param include_cargo: Set to True to include cargo handles in the graphical view.
    :param slats: Dictionary of slat objects (if not provided, will be generated from slat_array)
    :param save_to_folder: Set to the filepath of a folder where all figures will be saved.
    :param instant_view: Set to True to plot the figures immediately to your active view.
    :param filename_prepend: String to prepend to generated files.
    :param slat_width: The width to use for the slat lines.
    :param connection_angle: The angle of the slats in the design (either '90' or '60' for now).
    :return: N/A
    """

    num_layers = slat_array.shape[2]
    if slats is None:
        slats = convert_slat_array_into_slat_objects(slat_array)

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

    layers_containing_cargo = set()

    for slat_id, slat in slats.items():
        # TODO: Is there some way to print the slat ID in the graphic too?
        if len(slat.slat_coordinate_to_position) == 0:
            print(Fore.YELLOW + 'WARNING: Slat %s was ignored from graphical '
                                'view as it does not have a grid position defined.' % slat_id)
            continue

        if len(slat.slat_coordinate_to_position) != slat.max_length:
            print(Fore.YELLOW + 'WARNING: Slat %s was ignored from 2D graphical '
                                'view as it does not seem to have a normal set of grid coordinates.' % slat_id)
            continue

        start_pos = slat.slat_position_to_coordinate[1]
        end_pos = slat.slat_position_to_coordinate[slat.max_length]

        start_pos = physical_point_scale_convert(start_pos, grid_xd, grid_yd)  # this is necessary to ensure scaling is correct for 60deg angle slats
        end_pos = physical_point_scale_convert(end_pos, grid_xd, grid_yd)

        layer_color = layer_palette[slat.layer]['color']

        layer_figures[slat.layer - 1][1][0].plot([start_pos[1], end_pos[1]], [start_pos[0], end_pos[0]],
                                                 color=layer_color, linewidth=slat_width, zorder=1)
        layer_figures[slat.layer - 1][1][1].plot([start_pos[1], end_pos[1]], [start_pos[0], end_pos[0]],
                                                 color=layer_color, linewidth=slat_width, zorder=1)

        global_ax[0].plot([start_pos[1], end_pos[1]], [start_pos[0], end_pos[0]],
                          color=layer_color, linewidth=slat_width, alpha=0.5, zorder=slat.layer)
        global_ax[1].plot([start_pos[1], end_pos[1]], [start_pos[0], end_pos[0]],
                          color=layer_color, linewidth=slat_width, alpha=0.5, zorder=num_layers - slat.layer)

        handles = [slat.H5_handles, slat.H2_handles]
        sides = ['top' if layer_palette[slat.layer]['top'] == helix else 'bottom' for helix in [5, 2]]
        for handles, side in zip(handles, sides):
            for handle_index, handle in handles.items():
                coordinates = slat.slat_position_to_coordinate[handle_index]
                transformed_coords = [coordinates[0] * grid_yd, coordinates[1] * grid_xd]
                if handle['category'] == 'CARGO' and include_cargo:
                    layers_containing_cargo.add(slat.layer)
                    cargo_color = cargo_palette[handle['value']]['color']
                    layer_figures[slat.layer - 1][1][0 if side=='top' else 1].scatter(transformed_coords[1], transformed_coords[0],
                                                                             color=cargo_color,
                                                                             marker='s', s=100, zorder=10,
                                                                             label=handle['value'])

                    global_ax[0].scatter(transformed_coords[1], transformed_coords[0],
                                         color=cargo_color,
                                         s=100,
                                         marker='s', alpha=0.5, zorder=slat.layer, label=handle['value'])
                    global_ax[1].scatter(transformed_coords[1], transformed_coords[0],
                                         color=cargo_color,
                                         s=100, marker='s', alpha=0.5, zorder=num_layers - slat.layer,
                                         label=handle['value'])

                elif handle['category'] == 'SEED' and include_seed:
                    seed_color = cargo_palette['SEED']['color']
                    layer_figures[slat.layer - 1][1][0 if side=='top' else 1].scatter(transformed_coords[1], transformed_coords[0],
                                                                color=seed_color, s=100,
                                                                zorder=10)
                    global_ax[0].scatter(transformed_coords[1], transformed_coords[0], color=seed_color, s=100, alpha=0.5,
                                         zorder=slat.layer)
                    global_ax[1].scatter(transformed_coords[1], transformed_coords[0], color=seed_color, s=100, alpha=0.5,
                                         zorder=num_layers - slat.layer)

    if include_cargo:
        for layer in layers_containing_cargo:
            top_ax = layer_figures[layer - 1][1][0]
            bottom_ax = layer_figures[layer - 1][1][1]
            cargo_legend_setup(top_ax, bottom_ax)
        cargo_legend_setup(global_ax[0], global_ax[1])

    global_fig.tight_layout()
    if instant_view:
        global_fig.show()
    if save_to_folder:
        global_fig.savefig(os.path.join(save_to_folder, f'{filename_prepend}global_view.png'), dpi=300)

    for fig_ind, (fig, ax) in enumerate(layer_figures):
        fig.tight_layout()
        if instant_view:
            fig.show()
        if save_to_folder:
            fig.savefig(os.path.join(save_to_folder, '%slayer_%s.png' % (filename_prepend, fig_ind + 1)), dpi=300)
        plt.close(fig)


def create_graphical_assembly_handle_view(slat_array, handle_arrays, layer_palette,
                                          slats=None, save_to_folder=None, connection_angle='90',
                                          filename_prepend='',
                                          instant_view=True, slat_width=4):
    """
    Creates a graphical view of all handles in the assembled design, along with a side profile.
    :param slat_array: A 3D numpy array with x/y slat positions (slat ID placed in each position occupied)
    :param handle_arrays: A 3D numpy array with x/y handle positions (handle ID placed in each position occupied)
    :param layer_palette:
    :param slats: Dictionary of slat objects (if not provided, will be generated from slat_array)
    :param save_to_folder: Set to the filepath of a folder where all figures will be saved.
    :param connection_angle: The angle of the slats in the design (either '90' or '60' for now).
    :param filename_prepend: String to prepend to generated files.
    :param instant_view: Set to True to plot the figures immediately to your active view.
    :param slat_width: The width to use for the slat lines.
    :return: N/A
    """

    num_layers = slat_array.shape[2]
    if slats is None:
        slats = convert_slat_array_into_slat_objects(slat_array)

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

        if len(slat.slat_coordinate_to_position) != slat.max_length:
            print(Fore.YELLOW + 'WARNING: Slat %s was ignored from 2D assembly handle '
                                'view as it does not seem to have a normal set of grid coordinates.' % slat_id)
            continue

        start_pos = slat.slat_position_to_coordinate[1]
        end_pos = slat.slat_position_to_coordinate[slat.max_length]
        start_pos = physical_point_scale_convert(start_pos, grid_xd, grid_yd)  # this is necessary to ensure scaling is correct for 60deg angle slats
        end_pos = physical_point_scale_convert(end_pos, grid_xd, grid_yd)

        layer_color = layer_palette[slat.layer]['color']

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
    midway_v_point = ((slat_array.shape[0] + 1) / 2) * grid_yd
    full_v_scale = (slat_array.shape[0] + 1) * grid_yd
    full_x_scale = (slat_array.shape[1] + 1) * grid_xd

    if num_layers % 2 == 0:  # even and odd num of layers should have different spacing to remain centred
        start_point = midway_v_point - (layer_v_jump / 2) - (layer_v_jump * ((num_layers / 2) - 1) * full_v_scale)
    else:
        start_point = midway_v_point - (layer_v_jump * (math.floor(num_layers / 2)) * full_v_scale)

    for layer in range(num_layers):  # prepares actual lines here
        layer_lines.append([[-0.5 * grid_xd, (slat_array.shape[1] + 0.5) * grid_xd],
                            [start_point + (layer_v_jump * layer * full_v_scale),
                             start_point + (layer_v_jump * layer * full_v_scale)]])

    # layer lines are painted here, along with arrows and annotations
    annotation_vert_offset = 0.02
    annotation_vert_offset_btm = 0.026  # made a second offset scale here due to the way the font is positioned in the figure
    annotation_x_position = full_x_scale / 2
    for fig_ind, (fig, ax) in enumerate(interface_figures):
        for l_ind, line in enumerate(layer_lines):

            layer_color = layer_palette[l_ind + 1]['color']

            ax[1].plot(line[0], line[1], color=layer_color, linewidth=slat_width)

            # extracts interface numbers from megastructure data
            bottom_interface = layer_palette[l_ind+1]['bottom']
            top_interface = layer_palette[l_ind + 1]['top']

            ax[1].text(annotation_x_position, line[1][1] - (annotation_vert_offset_btm * full_v_scale),
                       'H%s' % bottom_interface, ha='center', va='center', color='black', zorder=3, fontsize=25,
                       weight='bold')
            ax[1].text(annotation_x_position, line[1][1] + (annotation_vert_offset * full_v_scale),
                       'H%s' % top_interface, ha='center', va='center', color='black', zorder=3, fontsize=25,
                       weight='bold')

        y_arrow_pos = layer_lines[fig_ind + 1][1][1] - (layer_lines[fig_ind + 1][1][1] - layer_lines[fig_ind][1][1]) / 2
        x_arrow_1 = -0.5 * grid_xd
        x_arrow_2 = (slat_array.shape[1] + 0.5) * grid_xd
        ax[1].arrow(x_arrow_1, y_arrow_pos, 0.1 * full_x_scale, 0, width=(0.8 * full_v_scale / 67), fc='k',
                    ec='k')  # arrow width was calibrated on a canvas with a vertical size of 67
        ax[1].arrow(x_arrow_2, y_arrow_pos, -0.1 * full_x_scale, 0, width=(0.8 * full_v_scale / 67), fc='k', ec='k')

    # final display and saving
    for fig_ind, (fig, ax) in enumerate(interface_figures):
        fig.tight_layout()
        if instant_view:
            fig.show()
        if save_to_folder:
            fig.savefig(os.path.join(save_to_folder,
                                     '%shandles_layer_%s_%s.png' % (filename_prepend, fig_ind + 1, fig_ind + 2)), dpi=300)
        plt.close(fig)
