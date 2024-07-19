import importlib
from colorama import Fore
import os
import matplotlib as mpl

from crisscross.core_functions.slats import convert_slat_array_into_slat_objects
from crisscross.helper_functions.slat_salient_quantities import connection_angles, slat_width

pyvista_spec = importlib.util.find_spec("pyvista")  # only imports pyvista if this is available
if pyvista_spec is not None:
    import pyvista as pv
    pyvista_available = True
else:
    pyvista_available = False


def create_graphical_3D_view(slat_array, save_folder, slats=None, connection_angle='90',
                             window_size=(2048, 2048), colormap='Set1'):
    """
    Creates a 3D video of a megastructure slat design. TODO: add cargo and seeds to this view too.
    :param slat_array: A 3D numpy array with x/y slat positions (slat ID placed in each position occupied)
    :param save_folder: Folder to save all video to.
    :param slats: Dictionary of slat objects (if not provided, will be generated from slat_array)
    :param connection_angle: The angle of the slats in the design (either '90' or '60' for now).
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

    plotter.add_axes(interactive=True)

    # Open a movie file
    plotter.open_movie(os.path.join(save_folder, '3D_design_view.mp4'))
    plotter.show(auto_close=False)

    # Again, it might be of interest to adjust parameters here for different designs
    path = plotter.generate_orbital_path(n_points=200, shift=0.2, viewup=[0, 1, 0], factor=2.0)
    plotter.orbit_on_path(path, write_frames=True, viewup=[0, 1, 0], step=0.05)
    plotter.close()
