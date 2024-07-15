# TODO: This file is still a work-in-progress
import importlib
from colorama import Fore
import os
import matplotlib as mpl
import numpy as np
import math

from crisscross.core_functions.slats import convert_slat_array_into_slat_objects
from crisscross.helper_functions.slat_salient_quantities import connection_angles, slat_width

bpy_spec = importlib.util.find_spec("bpy")  # only imports bpy if this is available
if bpy_spec is not None:
    import bpy
    import mathutils
    bpy_available = True
else:
    bpy_available = False
    print('The Blender API is not installed.  3D graphical views cannot be created using Blender.')


def look_at(obj, target):
    """
    Points the provided object towards the target vector
    :param obj: Blender object (typically a camera or light)
    :param target: The target 3D vector
    :return: N/A
    """
    direction = target - obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')  # I am not entirely sure how this works, but the 'Z' and 'Y' are basically there to make the object point in the right direction
    obj.rotation_euler = rot_quat.to_euler()


def create_slat_material(color, mat_name, metallic_strength=0.3):
    """
    :param color: RGB color code (4-value, with the last value being the alpha)
    :param mat_name: The name to assign to the material
    :param metallic_strength: How metallic the final material should be (default is slightly metallic)
    :return: The complete material object
    """

    material = bpy.data.materials.new(name=mat_name)
    material.use_nodes = True

    nodes = material.node_tree.nodes
    # Clear all nodes to start fresh
    for node in nodes:
        nodes.remove(node)

    # Add a Principled BSDF shader node (basic shader)
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Metallic'].default_value = metallic_strength

    # Add an Output node
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)  # spaces out the node a little bit
    # Connects the BSDF shader to Output node
    material.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return material


def set_slat_animation(frame_start, frame_end, slat_id, slat_cylinder, slat_center, slat_rotation, slat_length, hide_cube=True):
    """
    Sets up the animation for a single slat, which involves creating a cuboid and slowly covering the slat with the cuboid.
    :param frame_start: The frame from which to start the animation
    :param frame_end: The frame at which the animation ends
    :param slat_id: The slat's name
    :param slat_cylinder: The slat cylinder object pre-created in Blender
    :param slat_center: The center of the slat
    :param slat_rotation: The slat's orientation
    :param slat_length: The slat's length
    :param hide_cube: Set to true to hide the cover-cube from the viewport
    :return: N/A
    """
    # hide the slat initially
    bpy.context.object.hide_viewport = True
    bpy.context.object.keyframe_insert(data_path="hide_viewport", frame=0)

    # make the slat appear at the start of the animation (but will still be hidden by the cube)
    bpy.context.object.hide_viewport = False
    bpy.context.object.keyframe_insert(data_path="hide_viewport", frame=frame_start)

    # prepare cube to animate the slat's appearance
    bpy.ops.mesh.primitive_cube_add(location=slat_center, rotation=slat_rotation)
    cube = bpy.context.active_object
    cube.scale = (slat_width / 2, slat_width / 2, (slat_length / 2) + 1)

    cube.display_type = 'WIRE'
    cube.hide_render = True  # Set to be invisible in renders
    cube.name = slat_id + '-cube-cover'

    # sets up a difference modifier to the slat, which will power the slat animation system
    bool_modifier = slat_cylinder.modifiers.new(name="Boolean", type='BOOLEAN')
    bool_modifier.operation = 'DIFFERENCE'  # Set to 'DIFFERENCE'
    bool_modifier.object = cube  # Set the cube as the target object
    distance = slat_length + 2  # Distance to move the cube away from the cylinder

    # Get the cylinder's direction (z-axis)
    direction = mathutils.Vector((0, 0, 1))  # Assuming cylinder is aligned with Z-axis
    direction.rotate(mathutils.Euler(slat_rotation))  # Apply rotation

    # Set the initial keyframe
    initial_position = mathutils.Vector(slat_center)
    cube.location = initial_position
    cube.keyframe_insert(data_path="location", frame=frame_start)

    # Set the final position and keyframe (the cube will move slowly through the frames in between the start and end)
    final_position = initial_position + direction * distance
    cube.location = final_position
    cube.keyframe_insert(data_path="location", frame=frame_end)

    cube.hide_viewport = hide_cube


def check_slat_animation_direction(start_point, end_point, current_slat_id, current_layer, slats, animate_slat_group_dict):
    """
    Attempts a quick check to prevent slats from appearing 'out of thin air' but rather from a top/bottom support.
    :param start_point: The current slat start position
    :param end_point: The current slat end position
    :param current_slat_id: The current slat ID (name)
    :param current_layer: The slat's layer
    :param slats: The dict of all slats in the design
    :param animate_slat_group_dict: The dictionary of slat animation groups, in order
    :return: The new start and end position for the slat animation
    """

    current_group = animate_slat_group_dict[current_slat_id]
    if current_group == 0:
        return (start_point, end_point)  # no adjustments necessary if the slat is in the first group to be animated

    for slat_id, slat in slats.items():
        if animate_slat_group_dict[slat_id] < current_group:
            if start_point in slat.slat_coordinate_to_position and np.abs(slat.layer - current_layer) == 1:
                return (start_point, end_point)  # no adjustments necessary if the slat start point is covered by other slats (either directly above or below)

    # if the start point is never covered by any other slat, then it needs to be flipped with the end point for the animation to look nicer
    # there could be a case where the start point and end point both aren't covered, in which case the animation can come from either direction
    return (end_point, start_point)


def create_graphical_3D_view_bpy(slat_array, save_folder, slats=None, animate_slat_group_dict=None, animate_delay_frames=40,
                                 connection_angle='90', camera_spin=False, colormap='Set1'):
    """
    Creates a 3D video of a megastructure slat design. TODO: add cargo and seeds to this view too.
    :param slat_array: A 3D numpy array with x/y slat positions (slat ID placed in each position occupied)
    :param save_folder: Folder to save all video to.
    :param slats: Dictionary of slat objects (if not provided, will be generated from slat_array)
    :param connection_angle: The angle of the slats in the design (either '90' or '60' for now).
    :param camera_spin: Set to True to have the camera spin around the design
    :param colormap: Colormap to extract layer colors from
    :return: N/A
    """
    if not bpy_available:
        print(Fore.RED + 'The Blender Python API is not installed.  3D graphical views cannot be created using Blender.')
        return
    if slats is None:
        slats = convert_slat_array_into_slat_objects(slat_array)

    grid_xd, grid_yd = connection_angles[connection_angle][0], connection_angles[connection_angle][1]

    # Clear existing objects in the scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    materials = []
    for i in range(slat_array.shape[2]):
        color = mpl.colormaps[colormap].colors[i]
        materials.append(create_slat_material(color + (1,), f'Layer {i + 1}'))

    # prepares variables
    cylinder_min_boundaries = [np.inf, np.inf, np.inf]
    cylinder_max_boundaries = [0, 0, 0]
    max_frame = 0

    for slat_num, (slat_id, slat) in enumerate(slats.items()):

        pos1 = slat.slat_position_to_coordinate[1]  # first slat position
        pos2 = slat.slat_position_to_coordinate[32]  # second slat position

        if animate_slat_group_dict is not None:  # attempts to remove any conflicting animation directions
            pos1, pos2 = check_slat_animation_direction(pos1, pos2, slat_id, slat.layer, slats, animate_slat_group_dict)

        layer = slat.layer
        length = slat.max_length

        # Z-height is assumed to be precisely 1 for each layer - this could be changed to indicate the positions of assembly handles
        start_point = (pos1[1] * grid_xd, pos1[0] * grid_yd, layer - 1)
        end_point = (pos2[1] * grid_xd, pos2[0] * grid_yd, layer - 1)
        blender_vec_1 = mathutils.Vector(start_point)
        blender_vec_2 = mathutils.Vector(end_point)

        # Calculate the center and direction from start and end points
        center = ((start_point[0] + end_point[0]) / 2, (start_point[1] + end_point[1]) / 2, layer - 1)

        # updates the global boundaries of the model
        cylinder_min_boundaries = [min(s, e, b) for s, e, b in zip(start_point, end_point, cylinder_min_boundaries)]
        cylinder_max_boundaries = [max(s, e, b) for s, e, b in zip(start_point, end_point, cylinder_max_boundaries)]

        # computes the direction of the cylinder and the required orientation
        direction = (blender_vec_2 - blender_vec_1).normalized()
        up = mathutils.Vector((0, 0, 1))
        rotation = up.rotation_difference(direction).to_euler()

        # creates the cylinder then obtains a reference to it for further processing
        bpy.ops.mesh.primitive_cylinder_add(location=center, radius=slat_width/2, rotation=rotation, depth=length)
        cylinder = bpy.context.active_object

        # sets the cylinder's name, makes sure the shading is smooth, and sets the material
        bpy.context.object.name = slat_id
        bpy.ops.object.shade_smooth()
        bpy.context.object.data.materials.append(materials[layer - 1])

        if animate_slat_group_dict is not None:
            frame_start = animate_slat_group_dict[slat_id] * animate_delay_frames
            frame_end = frame_start + animate_delay_frames
            max_frame = max(max_frame, frame_end)  # tracks the maximum amount of frames in the animation
            set_slat_animation(frame_start, frame_end, slat_id, cylinder, center, rotation, length, hide_cube=True)

    if animate_slat_group_dict is not None:
        bpy.context.scene.frame_end = max_frame

    # calculate the maximum dimensions of the entire assembly of slats
    design_widths = [cylinder_max_boundaries[0] + cylinder_min_boundaries[0], cylinder_max_boundaries[1] + cylinder_min_boundaries[1]]
    design_height = cylinder_max_boundaries[2]

    # Create and position a big area light to illuminate the whole model
    bpy.ops.object.light_add(type='AREA', location=(design_widths[0]/2, design_widths[1]/2, design_height + 20))
    area_light = bpy.context.object
    area_light.name = "Main Crisscross Spotlight"
    area_light.data.energy = 40000
    area_light.data.size = max(design_widths) * 1.5

    # Point the area light at the center of the design
    look_at(area_light, mathutils.Vector((design_widths[0]/2, design_widths[1]/2, design_height/2)))

    # Create a camera with a wide enough view to encompass the entire design
    bpy.ops.object.camera_add(location=(design_widths[0]/2, -10, design_height + 45))
    camera = bpy.context.object
    camera.name = "Main Camera"

    # Point the camera at the center of the design
    look_at(camera, mathutils.Vector((design_widths[0]/2, design_widths[1]/2, design_height/2)))

    # Calculate the distance from the camera to the center of the scene
    cam_distance = (camera.location.x - design_widths[0]/2, camera.location.y - design_widths[1]/2, camera.location.z - design_height/2)
    cam_distance = np.sqrt(cam_distance[0]**2 + cam_distance[1]**2 + cam_distance[2]**2)

    # Calculate the required sensor FOV
    scene_width = max(design_widths)
    sensor_fov_angle = 2 * math.atan(scene_width / (2 * cam_distance)) # this attempts to calculate the best FOV considering the target object width and distance, but I'm not sure if it's accurate yet
    sensor_fov_angle = sensor_fov_angle * (1920/1080)  # an attempt to adjust for the output aspect ratio, but I'm not 100% sure on this yet

    # The camera's FOV angle and main camera setting is set here
    camera.data.angle = sensor_fov_angle
    bpy.context.scene.camera = camera

    if camera_spin:
        # Create an empty object at the center of the design
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=mathutils.Vector((design_widths[0]/2, design_widths[1]/2, design_height/2)))
        empty = bpy.context.object

        # Parent the camera to the empty object
        camera.select_set(True)
        empty.select_set(True)
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
        empty.select_set(False)

        # Define animation parameters
        frame_start = 0
        frame_end = max_frame
        rotation_degrees = 360  # Full rotation

        # Set the keyframes for the empty object's rotation - the camera will follow it as it rotates
        empty.rotation_euler = (0, 0, 0)
        empty.keyframe_insert(data_path="rotation_euler", frame=frame_start)

        empty.rotation_euler = (0, 0, np.deg2rad(rotation_degrees))
        empty.keyframe_insert(data_path="rotation_euler", frame=frame_end)

        # Set the animation interpolation to linear
        for fcurve in empty.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = 'LINEAR'

    # Ensures the view mode is updated
    bpy.context.view_layer.update()

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(save_folder, '3D_blender_view.blend'))

