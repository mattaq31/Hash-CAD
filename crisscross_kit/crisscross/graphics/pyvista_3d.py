import importlib
from colorama import Fore
import os
from collections import defaultdict

from crisscross.core_functions.slats import convert_slat_array_into_slat_objects
from crisscross.helper_functions.slat_salient_quantities import connection_angles, slat_width

pyvista_spec = importlib.util.find_spec("pyvista")  # only imports pyvista if this is available
if pyvista_spec is not None:
    import pyvista as pv
    pv.OFF_SCREEN = True # Enables off-screen rendering (to allow graphics generation when not using the main thread)
    pyvista_available = True
else:
    pyvista_available = False


def create_graphical_3D_view(slat_array, slats, save_folder, layer_palette, cargo_palette=None,
                              connection_angle='90', window_size=(2048, 2048), filename_prepend=''):
    """
    Creates a 3D video of a megastructure slat design.
    :param slat_array: A 3D numpy array with x/y slat positions (slat ID placed in each position occupied)
    :param slats: Dictionary of slat objects
    :param save_folder: Folder to save all video to.
    :param layer_palette: Dictionary of layer information (e.g. top/bottom helix and colors), where keys are layer numbers.
    :param cargo_palette: Dictionary of cargo information (e.g. colors), where keys are cargo types.
    :param connection_angle: The angle of the slats in the design (either '90' or '60' for now).
    :param window_size: Resolution of video generated.  2048x2048 seems reasonable in most cases.
    :param filename_prepend: String to prepend to the filename of the video.
    :return: N/A
    """
    if not pyvista_available:
        print(Fore.RED + 'Pyvista not installed.  3D graphical views cannot be created.' + Fore.RESET)
        return

    if slats is None:
        slats = convert_slat_array_into_slat_objects(slat_array)
    grid_yd, grid_xd = connection_angles[connection_angle][0], connection_angles[connection_angle][1]

    plotter = pv.Plotter(window_size=window_size, off_screen=True)

    seed_coord_dict = defaultdict(dict)

    for slat_id, slat in slats.items():  # Z-height is set to 1 here, could be interested in changing in some cases
        if len(slat.slat_position_to_coordinate) == 0:
            print(Fore.YELLOW + f'WARNING: Slat {slat_id} was ignored from 3D graphical '
                                'view as it does not have a grid position defined.' + Fore.RESET)
            continue

        pos1 = slat.slat_position_to_coordinate[1]
        pos2 = slat.slat_position_to_coordinate[slat.max_length]

        layer = slat.layer
        length = slat.max_length
        main_color = slat.unique_color if slat.unique_color is not None else layer_palette[layer]['color']

        # TODO: can we represent the cylinders with the precise dimensions of the real thing i.e. with the 12/6nm extension on either end?
        start_point = (pos1[0] * grid_xd, pos1[1] * grid_yd, layer - 1)
        end_point = (pos2[0] * grid_xd, pos2[1] * grid_yd, layer - 1)

        # Calculate the center and direction from start and end points
        center = ((start_point[0] + end_point[0]) / 2, (start_point[1] + end_point[1]) / 2, layer - 1)
        direction = (end_point[0] - start_point[0], end_point[1] - start_point[1], end_point[2] - start_point[2])

        # Create the cylinder
        cylinder = pv.Cylinder(center=center, direction=direction, radius=slat_width/2, height=length)
        plotter.add_mesh(cylinder, color=main_color)

        handles = [slat.H5_handles, slat.H2_handles]
        sides = ['top' if layer_palette[slat.layer]['top'] == helix else 'bottom' for helix in [5, 2]]

        for handles, side in zip(handles, sides):
            if side == 'top':
                top_or_bottom = 1
            else:
                top_or_bottom = -1

            for handle_index, handle in handles.items():
                # gathers cargo data and applies cargo positions as small cylinders
                if handle['category'] == 'CARGO':
                    coordinates = slat.slat_position_to_coordinate[handle_index]
                    transformed_coords = [coordinates[0] * grid_xd, coordinates[1] * grid_yd]
                    transformed_pos = (transformed_coords[0], transformed_coords[1], slat.layer - 1 + (top_or_bottom * slat_width / 2))

                    cylinder = pv.Cylinder(center=transformed_pos, direction=(0, 0, top_or_bottom), radius=slat_width / 2,
                                           height=slat_width)
                    plotter.add_mesh(cylinder, color=cargo_palette[handle['value']]['color'])

                # gathers seed data for later plotting
                elif handle['category'] == 'SEED':
                    coordinates = slat.slat_position_to_coordinate[handle_index]
                    transformed_coords = [coordinates[0] * grid_xd, coordinates[1] * grid_yd]
                    r, c =  handle['value'].split('_')
                    seed_id = handle['descriptor'].split('|')[-1]
                    if c == '1':
                        seed_coord_dict['start_coords'][f'{seed_id}-{r}'] = (slat.layer - 1 + top_or_bottom, transformed_coords[0], transformed_coords[1])
                    elif c == '16':
                        seed_coord_dict['end_coords'][f'{seed_id}-{r}'] = (slat.layer - 1 + top_or_bottom, transformed_coords[0], transformed_coords[1])

    # runs through the standard slat cylinder creation process, creating 5 cylinders for each seed
    for key in seed_coord_dict['start_coords'].keys():

        s_coord = seed_coord_dict['start_coords'][key]
        e_coord = seed_coord_dict['end_coords'][key]

        seed_start = (s_coord[1], s_coord[2], s_coord[0])
        seed_end = (e_coord[1], e_coord[2], e_coord[0])

        # Calculate the center and direction from start and end points
        center = ((seed_start[0] + seed_end[0]) / 2, (seed_start[1] + seed_end[1]) / 2, s_coord[0])
        direction = (seed_end[0] - seed_start[0], seed_end[1] - seed_start[1], seed_end[2] - seed_start[2])

        # Create the cylinder
        cylinder = pv.Cylinder(center=center, direction=direction, radius=slat_width / 2, height=16)
        plotter.add_mesh(cylinder, color=cargo_palette['SEED']['color'])

    plotter.add_axes(interactive=False)

    # Open a movie file
    plotter.open_movie(os.path.join(save_folder, f'{filename_prepend}3D_design_view.mp4'))

    # It might be of interest to adjust parameters here for different designs
    path = plotter.generate_orbital_path(n_points=200, shift=0.2, viewup=[0, -1, 0], factor=2.0)
    plotter.orbit_on_path(path, write_frames=True, viewup=[0, -1, 0], step=0.05)
    plotter.close()
