import importlib
from colorama import Fore
import os
import numpy as np
from collections import defaultdict
import math

from crisscross.core_functions.slats import convert_slat_array_into_slat_objects
from crisscross.helper_functions.slat_salient_quantities import connection_angles, slat_width

pyvista_spec = importlib.util.find_spec("pyvista")  # only imports pyvista if this is available
if pyvista_spec is not None:
    import pyvista as pv
    pv.OFF_SCREEN = True # Enables off-screen rendering (to allow graphics generation when not using the main thread)
    pyvista_available = True
else:
    pyvista_available = False

def rounded_polyline(points, corner_fraction=0.45, samples_per_corner=16, uturn_angle_threshold_deg=170.0):
    """
    Replace interior corners with fillets; handles three cases:
      - nearly-straight: pass-through
      - normal corner: quadratic Bezier fillet (A..P1..B)
      - near-180° (U-turn): generate a true semicircular arc across p1
    Returns np.array((M,3)).
    """
    pts = np.asarray(points, dtype=float)
    n = len(pts)
    if n <= 2:
        return pts

    new_pts = [pts[0].tolist()]
    eps = 1e-12
    # cosine threshold for U-turn detection
    cos_uturn = np.cos(np.deg2rad(uturn_angle_threshold_deg))

    for i in range(1, n - 1):
        p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
        v_in = p1 - p0
        v_out = p2 - p1
        len_in = np.linalg.norm(v_in)
        len_out = np.linalg.norm(v_out)
        if len_in < eps or len_out < eps:
            new_pts.append(p1.tolist())
            continue

        u_in = v_in / len_in
        u_out = v_out / len_out
        dot = np.dot(u_in, u_out)

        # nearly straight
        if dot > 0.999:
            new_pts.append(p1.tolist())
            continue

        # compute fillet run distance
        d = corner_fraction * min(len_in, len_out)
        d = max(min(d, 0.5 * len_in, 0.5 * len_out), 0.0)
        if d <= eps:
            new_pts.append(p1.tolist())
            continue

        # strong U-turn: dot < cos_uturn (i.e. angle > uturn_angle_threshold_deg)
        if dot < cos_uturn:
            # Build a semicircle in the plane of u_in and some perpendicular (binormal).
            # Use endpoints A = p1 - u_in * r  and  B = p1 + u_in * r
            r = d
            A = p1 - u_in * r
            B = p1 + u_in * r

            # pick a stable perpendicular direction for the bending plane
            normal = np.cross(u_in, np.array([0.0, 0.0, 1.0]))
            if np.linalg.norm(normal) < 1e-8:
                normal = np.cross(u_in, np.array([0.0, 1.0, 0.0]))
            normal /= np.linalg.norm(normal)
            binormal = np.cross(normal, u_in)
            binorm_len = np.linalg.norm(binormal)
            if binorm_len < 1e-12:
                # fallback: arbitrary perpendicular
                binormal = np.array([-u_in[1], u_in[0], 0.0])
                binorm_len = np.linalg.norm(binormal)
                if binorm_len < 1e-12:
                    # give up and just keep point
                    new_pts.append(p1.tolist())
                    continue
            binormal /= binorm_len

            # semicircle param t in [0, pi]
            thetas = np.linspace(0.0, np.pi, samples_per_corner + 2)[1:-1]
            # add A explicitly first so consistent with other fillets
            new_pts.append(A.tolist())
            for theta in thetas:
                q = p1 - u_in * r * np.cos(theta) + binormal * r * np.sin(theta)
                new_pts.append(q.tolist())
            new_pts.append(B.tolist())
            continue

        # normal corner -> quadratic Bezier fillet between A and B
        A = p1 - u_in * d
        B = p1 + u_out * d
        new_pts.append(A.tolist())
        ts = np.linspace(0.0, 1.0, samples_per_corner + 2)[1:-1]
        for t in ts:
            q = (1 - t) ** 2 * A + 2 * (1 - t) * t * p1 + t ** 2 * B
            new_pts.append(q.tolist())
        new_pts.append(B.tolist())

    new_pts.append(pts[-1].tolist())
    return np.array(new_pts)


def parallel_transport_frames(points):
    """Compute tangent, normal, binormal at each point using parallel transport.
    Returns (tangents, normals, binormals) arrays same length as points.
    """
    pts = np.asarray(points, dtype=float)
    n = len(pts)
    tangents = np.zeros((n, 3), dtype=float)
    for i in range(n):
        if i == 0:
            v = pts[1] - pts[0]
        elif i == n - 1:
            v = pts[-1] - pts[-2]
        else:
            v = pts[i + 1] - pts[i - 1]
        norm = np.linalg.norm(v)
        tangents[i] = v / (norm + 1e-12)

    # initial normal: pick any vector not parallel to t0
    t0 = tangents[0]
    up = np.array([0.0, 0.0, 1.0])
    if abs(np.dot(t0, up)) > 0.99:
        up = np.array([0.0, 1.0, 0.0])
    n0 = np.cross(up, t0)
    n0 /= np.linalg.norm(n0) + 1e-12

    normals = np.zeros_like(tangents)
    binormals = np.zeros_like(tangents)
    normals[0] = n0
    binormals[0] = np.cross(tangents[0], normals[0])
    # transport
    for i in range(1, n):
        t_prev = tangents[i - 1]
        t_cur = tangents[i]
        cross_t = np.cross(t_prev, t_cur)
        cross_norm = np.linalg.norm(cross_t)
        if cross_norm < 1e-12:
            # almost colinear: keep previous normal
            normals[i] = normals[i - 1]
        else:
            axis = cross_t / cross_norm
            cosang = np.dot(t_prev, t_cur)
            cosang = max(min(cosang, 1.0), -1.0)
            angle = math.acos(cosang)
            # Rodrigues rotation of previous normal about axis by angle
            v = normals[i - 1]
            v_rot = (v * math.cos(angle) +
                     np.cross(axis, v) * math.sin(angle) +
                     axis * (np.dot(axis, v)) * (1.0 - math.cos(angle)))
            normals[i] = v_rot / (np.linalg.norm(v_rot) + 1e-12)
        binormals[i] = np.cross(tangents[i], normals[i])
        bn = np.linalg.norm(binormals[i])
        if bn > 1e-12:
            binormals[i] /= bn
    return tangents, normals, binormals


def build_swept_tube(curve_pts, radius, n_sides=32, cap_ends=False):
    """
    Build a tube mesh by sweeping a circle along curve_pts using parallel-transport frames.
    Returns a pyvista.PolyData mesh.
    """
    pts = np.asarray(curve_pts, dtype=float)
    tangents, normals, binormals = parallel_transport_frames(pts)
    n_rings = len(pts)
    verts = []
    for i in range(n_rings):
        for j in range(n_sides):
            theta = 2.0 * math.pi * j / n_sides
            offset = normals[i] * math.cos(theta) + binormals[i] * math.sin(theta)
            verts.append(pts[i] + radius * offset)
    verts = np.array(verts, dtype=float)

    # build triangle faces between successive rings
    faces = []
    for i in range(n_rings - 1):
        base = i * n_sides
        base_next = (i + 1) * n_sides
        for j in range(n_sides):
            a = base + j
            b = base + ((j + 1) % n_sides)
            c = base_next + ((j + 1) % n_sides)
            d = base_next + j
            # two triangles (a, b, c) and (a, c, d)
            faces.append([3, a, b, c])
            faces.append([3, a, c, d])

    # optional end caps (fan triangles)
    if cap_ends:
        # start cap
        center_start_idx = verts.shape[0]
        center_start = pts[0].tolist()
        verts = np.vstack([verts, center_start])
        for j in range(n_sides):
            a = j
            b = (j + 1) % n_sides
            faces.append([3, center_start_idx, b, a])  # winding such that normal points outward

        # end cap
        center_end_idx = verts.shape[0]
        center_end = pts[-1].tolist()
        verts = np.vstack([verts, center_end])
        last_ring = (n_rings - 1) * n_sides
        for j in range(n_sides):
            a = last_ring + j
            b = last_ring + ((j + 1) % n_sides)
            faces.append([3, center_end_idx, a, b])

    faces = np.hstack(faces).astype(np.int64)
    mesh = pv.PolyData(verts, faces)
    # compute normals for nice shading
    mesh.compute_normals(cell_normals=False, point_normals=True, inplace=True, auto_orient_normals=True)
    return mesh

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
        if slat.phantom_parent is not None: continue # for now, will not be including phantom slats in graphics
        if len(slat.slat_position_to_coordinate) == 0:
            print(Fore.YELLOW + f'WARNING: Slat {slat_id} was ignored from 3D graphical '
                                'view as it does not have a grid position defined.' + Fore.RESET)
            continue

        # Ensure the slat looks continuous
        if len(slat.slat_position_to_coordinate) != slat.max_length:
            print(Fore.YELLOW + f'WARNING: Slat {slat_id} was ignored from 3D graphical '
                                'view as it does not seem to have a normal set of grid coordinates.' + Fore.RESET)
            continue

        layer = slat.layer
        main_color = slat.unique_color if slat.unique_color is not None else layer_palette[layer]['color']

        # TODO: can we represent the cylinders with the precise dimensions of the real thing i.e. with the 12/6nm extension on either end?

        # Build the full points path of the entire slat
        points = []
        for i in range(1, slat.max_length + 1):
            r, c = slat.slat_position_to_coordinate[i]
            x = r * grid_xd
            y = c * grid_yd
            z = layer - 1
            # dedupe consecutive duplicates (prevents zero-length tube segments)
            if not points or (x, y, z) != tuple(points[-1]):
                points.append([x, y, z])

        # add additional points to smooth corners if required  (e.g. for double-barrel slats)
        curve = rounded_polyline(points, corner_fraction=0.45, samples_per_corner=10)

        # Build the tube manually using parallel transport frames to avoid 'pizza' seams
        radius = slat_width / 2.0
        n_sides = 28  # tune for smoothness vs performance
        tube_mesh = build_swept_tube(curve, radius=radius, n_sides=n_sides, cap_ends=False)

        # Add the final result to the 3D scene
        plotter.add_mesh(tube_mesh, color=main_color, smooth_shading=True)

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
