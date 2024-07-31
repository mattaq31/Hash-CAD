import importlib
from colorama import Fore
import os
import matplotlib as mpl
import numpy as np

from crisscross.core_functions.slats import convert_slat_array_into_slat_objects
from crisscross.helper_functions.slat_salient_quantities import connection_angles, slat_width

pyvista_spec = importlib.util.find_spec("pyvista")  # only imports pyvista if this is available
if pyvista_spec is not None:
    import pyvista as pv
    pyvista_available = True
else:
    pyvista_available = False


def interpret_seed_system(seed_layer_and_array, seed_length, grid_xd, grid_yd, seed_color, pyvista_plotter):
    """
    Interprets the seed array and places seed cylinders in the 3D scene.
    Makes the assumption that np.where can correctly figure out where each seed cylinder starts/stops.
    If there are errors here, this will need to be fixed.
    :param seed_layer_and_array: A tuple of the layer the seed is attached to and the seed position array
    :param seed_length: The length of each seed cylinder
    :param grid_xd: The grid x-jump distance
    :param grid_yd: The grid y-jump distance
    :param seed_color: The color to use for the seed cylinders
    :param pyvista_plotter: The pyvista plotter object to which cylinders are added
    :return: N/A
    """

    layer = seed_layer_and_array[0]-1  # -1 as the seed is underneath the particular slat layer TODO: this assumption might not always be correct
    seed_array = seed_layer_and_array[1]

    start_points = np.where(seed_array == 1)  # assumes np.where can correctly order the different start/end points
    end_points = np.where(seed_array == 16)

    # runs through the standard slat cylinder creation process, creating 5 cylinders for each seed
    for index, (sx, sy, ex, ey) in enumerate(zip(start_points[0], start_points[1], end_points[0], end_points[1])):
        pos1 = (sx, sy)
        pos2 = (ex, ey)

        start_point = (pos1[1] * grid_xd, pos1[0] * grid_yd, layer - 1)
        end_point = (pos2[1] * grid_xd, pos2[0] * grid_yd, layer - 1)

        # Calculate the center and direction from start and end points
        center = ((start_point[0] + end_point[0]) / 2, (start_point[1] + end_point[1]) / 2, layer - 1)
        direction = (end_point[0] - start_point[0], end_point[1] - start_point[1], end_point[2] - start_point[2])

        # Create the cylinder
        cylinder = pv.Cylinder(center=center, direction=direction, radius=slat_width/2, height=seed_length)
        pyvista_plotter.add_mesh(cylinder, color=seed_color)


def create_graphical_3D_view(slat_array, save_folder, slats=None, connection_angle='90', seed_layer_and_array=None,
                             seed_color=(1.0, 0.0, 0.0), cargo_dict=None, layer_interface_orientations=None,
                             cargo_colormap='Dark2', window_size=(2048, 2048), colormap='Set1'):
    """
    Creates a 3D video of a megastructure slat design.
    :param slat_array: A 3D numpy array with x/y slat positions (slat ID placed in each position occupied)
    :param save_folder: Folder to save all video to.
    :param slats: Dictionary of slat objects (if not provided, will be generated from slat_array)
    :param connection_angle: The angle of the slats in the design (either '90' or '60' for now).
    :param seed_layer_and_array: Provide a tuple of the seed layer and its position array to add seed cylinders to the 3D video.
    :param seed_color: Color of the seed cylinders.
    :param cargo_dict: Provide the cargo dictionary to add cargo cylinders to the 3D video.
    :param layer_interface_orientations: This is a dictionary of the layer interface orientations (top/bottom) for each layer.
    Required to generate cargo cylinders.
    :param cargo_colormap: Colormap to extract cargo colors from.
    :param window_size: Resolution of video generated.  2048x2048 seems reasonable in most cases.
    :param colormap: Colormap to extract layer colors from
    :return: N/A
    """
    if not pyvista_available:
        print(Fore.RED + 'Pyvista not installed.  3D graphical views cannot be created.')
        return

    if slats is None:
        slats = convert_slat_array_into_slat_objects(slat_array)
    grid_xd, grid_yd = connection_angles[connection_angle][0], connection_angles[connection_angle][1]

    plotter = pv.Plotter(window_size=window_size, off_screen=True)

    for slat_id, slat in slats.items():  # Z-height is set to 1 here, could be interested in changing in some cases
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
        start_point = (pos1[1] * grid_xd, pos1[0] * grid_yd, layer - 1)
        end_point = (pos2[1] * grid_xd, pos2[0] * grid_yd, layer - 1)

        # Calculate the center and direction from start and end points
        center = ((start_point[0] + end_point[0]) / 2, (start_point[1] + end_point[1]) / 2, layer - 1)
        direction = (end_point[0] - start_point[0], end_point[1] - start_point[1], end_point[2] - start_point[2])

        # Create the cylinder
        cylinder = pv.Cylinder(center=center, direction=direction, radius=slat_width/2, height=length)
        plotter.add_mesh(cylinder, color=layer_color)

    if cargo_dict is not None and layer_interface_orientations is not None:
        # sets the colours of annotation according to the cargo being added
        all_cargo = set(cargo_dict.values())
        cargo_color_values_rgb = {}
        for cargo_number, unique_cargo_name in enumerate(sorted(all_cargo)):
            if cargo_number >= len(mpl.colormaps[cargo_colormap].colors):
                print(Fore.RED + 'WARNING: Cargo ID %s is out of range for the 3D structure colormap. '
                                 'Recycling other colors for the higher IDs.' % unique_cargo_name)
                cargo_number = max(int(cargo_number) - len(mpl.colormaps[cargo_colormap].colors), 0)
            cargo_color_values_rgb[unique_cargo_name] = (mpl.colormaps[cargo_colormap].colors[cargo_number])

        for ((y_cargo, x_cargo), cargo_layer, cargo_orientation), cargo_value in cargo_dict.items():

            top_layer_side = layer_interface_orientations[cargo_layer]
            if isinstance(top_layer_side, tuple):
                top_layer_side = top_layer_side[0]
            if top_layer_side == cargo_orientation:
                top_or_bottom = 1
            else:
                top_or_bottom = -1

            transformed_pos = (x_cargo * grid_xd, y_cargo * grid_yd, cargo_layer - 1 + (top_or_bottom*slat_width/2))

            cylinder = pv.Cylinder(center=transformed_pos, direction=(0, 0, top_or_bottom), radius=slat_width / 2, height=slat_width)
            plotter.add_mesh(cylinder, color=cargo_color_values_rgb[cargo_value])

    interpret_seed_system(seed_layer_and_array, list(slats.values())[0].max_length/2, grid_xd, grid_yd, seed_color, plotter)

    plotter.add_axes(interactive=True)

    # Open a movie file
    plotter.open_movie(os.path.join(save_folder, '3D_design_view.mp4'))
    plotter.show(auto_close=False)

    # Again, it might be of interest to adjust parameters here for different designs
    path = plotter.generate_orbital_path(n_points=200, shift=0.2, viewup=[0, 1, 0], factor=2.0)
    plotter.orbit_on_path(path, write_frames=True, viewup=[0, 1, 0], step=0.05)
    plotter.close()
