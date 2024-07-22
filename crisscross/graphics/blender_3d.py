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


def create_slat_material(color, mat_name, metallic_strength=0.3, alpha_animation=False):
    """
    :param color: RGB color code (4-value, with the last value being the alpha)
    :param mat_name: The name to assign to the material
    :param metallic_strength: How metallic the final material should be (default is slightly metallic)
    :param alpha_animation: Set to True to enable alpha animation (for slat wipe-in animations)
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

    if alpha_animation:
        material.blend_method = 'BLEND'  # Alpha Blend
        material.use_backface_culling = True  # turns off backface visibility

    return material


def set_slat_wipe_in_animation(frame_start, frame_end, slat_id, slat_cylinder, slat_center, slat_rotation, slat_length, hide_cube=True):
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


def set_slat_translate_animation(frame_start, frame_end, slat_cylinder, slat_center, slat_rotation, slat_length,
                                 extension_length=2):
    """
    Sets up a translation-based entry animation for a slat
    :param frame_start: The frame from which to start the animation
    :param frame_end: The frame at which the animation ends
    :param slat_cylinder: The slat cylinder object pre-created in Blender
    :param slat_center: The center of the slat
    :param slat_rotation: The slat's orientation
    :param slat_length: The slat's length
    :param extension_length: The distance that the slat will move to complete the animation
    :return: N/A
    """

    # Get the cylinder's direction (z-axis)
    direction = mathutils.Vector((0, 0, 1))  # Assuming cylinder is aligned with Z-axis
    direction.rotate(mathutils.Euler(slat_rotation))  # Apply rotation

    # Set the final keyframe (slat in place)
    final_position = mathutils.Vector(slat_center)
    slat_cylinder.location = final_position
    slat_cylinder.keyframe_insert(data_path="location", frame=frame_end)

    # Set the initial position and keyframe (the cylinder will move slowly through the frames in between the start and end)
    distance = slat_length + extension_length  # Distance to move the cylinder
    initial_position = final_position + direction * distance
    slat_cylinder.location = initial_position
    slat_cylinder.keyframe_insert(data_path="location", frame=frame_start+5)

    # get the slat's shader node
    nodes = slat_cylinder.data.materials[0].node_tree.nodes
    principled_node = None
    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            principled_node = node
            break

    # ensures the slat is transparent until it is called for in the animation
    principled_node.inputs['Alpha'].default_value = 0.0
    principled_node.inputs['Alpha'].keyframe_insert(data_path="default_value", frame=1)
    principled_node.inputs['Alpha'].default_value = 0.0
    principled_node.inputs['Alpha'].keyframe_insert(data_path="default_value", frame=frame_start)

    # have the slat appear fully at the start of the animation
    principled_node.inputs['Alpha'].default_value = 1.0
    principled_node.inputs['Alpha'].keyframe_insert(data_path="default_value", frame=frame_start+5)

    slat_cylinder.data.materials[0].blend_method = 'BLEND'  # turn on alpha blend
    slat_cylinder.data.materials[0].keyframe_insert(data_path="blend_method", frame=1)

    slat_cylinder.data.materials[0].blend_method = 'OPAQUE'  # turn off alpha blend
    slat_cylinder.data.materials[0].keyframe_insert(data_path="blend_method", frame=frame_end)

    # turn off slat entirely before the animation to ensure it doesn't interfere with the
    # other objects (due to alpha blend)
    slat_cylinder.hide_render = True
    slat_cylinder.hide_viewport = True
    slat_cylinder.keyframe_insert(data_path="hide_render", frame=0)
    slat_cylinder.keyframe_insert(data_path="hide_viewport", frame=0)

    slat_cylinder.hide_render = False
    slat_cylinder.hide_viewport = False
    slat_cylinder.keyframe_insert(data_path="hide_render", frame=frame_start)
    slat_cylinder.keyframe_insert(data_path="hide_viewport", frame=frame_start)


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
        return start_point, end_point  # no adjustments necessary if the slat is in the first group to be animated

    for slat_id, slat in slats.items():
        if animate_slat_group_dict[slat_id] < current_group:
            if start_point in slat.slat_coordinate_to_position and np.abs(slat.layer - current_layer) == 1:
                return start_point, end_point  # no adjustments necessary if the slat start point is covered by other slats (either directly above or below)

    # if the start point is never covered by any other slat, then it needs to be flipped with the end point for the animation to look nicer
    # there could be a case where the start point and end point both aren't covered, in which case the animation can come from either direction
    return end_point, start_point


def interpret_seed_system(seed_layer_and_array, seed_material, seed_length, grid_xd, grid_yd):
    """
    Interprets the seed array and places seed cylinders in the Blender scene.
    Makes the assumption that np.where can correctly figure out where each seed cylinder starts/stops.
    If there are errors here, this will need to be fixed.
    :param seed_layer_and_array: A tuple of the layer the seed is attached to and the seed position array
    :param seed_material: The material to use for the seed
    :param seed_length: The length of each seed cylinder
    :param grid_xd: The grid x-jump distance
    :param grid_yd: The grid y-jump distance
    :return: N/A
    """

    layer = seed_layer_and_array[0]-1  # -1 as the seed is underneath the particular slat layer
    seed_array = seed_layer_and_array[1]

    start_points = np.where(seed_array == 1)  # assumes np.where can correctly order the different start/end points
    end_points = np.where(seed_array == 16)

    # runs through the standard slat cylinder creation process, creating 5 cylinders for each seed
    for index, (sx, sy, ex, ey) in enumerate(zip(start_points[0], start_points[1], end_points[0], end_points[1])):
        pos1 = (sx, sy)
        pos2 = (ex, ey)

        start_point = (pos1[1] * grid_xd, pos1[0] * grid_yd, layer - 1)
        end_point = (pos2[1] * grid_xd, pos2[0] * grid_yd, layer - 1)
        blender_vec_1 = mathutils.Vector(start_point)
        blender_vec_2 = mathutils.Vector(end_point)

        center = ((start_point[0] + end_point[0]) / 2, (start_point[1] + end_point[1]) / 2, layer - 1)

        direction = (blender_vec_2 - blender_vec_1).normalized()
        up = mathutils.Vector((0, 0, 1))
        rotation = up.rotation_difference(direction).to_euler()

        bpy.ops.mesh.primitive_cylinder_add(location=center, radius=slat_width / 2, rotation=rotation, depth=seed_length)
        bpy.context.object.name = 'seed-%s' % index
        bpy.ops.object.shade_smooth()
        bpy.context.object.data.materials.append(seed_material)


def create_graphical_3D_view_bpy(slat_array, save_folder, slats=None, animate_slat_group_dict=None,
                                 animate_delay_frames=40, connection_angle='90', seed_layer_and_array=None,
                                 camera_spin=False, animation_type='translate', specific_slat_translate_distances=None,
                                 colormap='Set1'):
    """
    Creates a 3D video of a megastructure slat design. TODO: add cargo to this view too.
    :param slat_array: A 3D numpy array with x/y slat positions (slat ID placed in each position occupied)
    :param save_folder: Folder to save all video to.
    :param slats: Dictionary of slat objects (if not provided, will be generated from slat_array)
    :param animate_slat_group_dict: Dictionary of slat IDs and the group they belong to for animation
    :param animate_delay_frames: Number of frames to delay between each slat group animation
    :param connection_angle: The angle of the slats in the design (either '90' or '60' for now).
    :param seed_layer_and_array: Tuple of the seed layer and seed array to be added to the design (or None if no seed to be added)
    :param camera_spin: Set to True to have the camera spin around the design
    :param animation_type: The type of animation to use for slat entry ('translate' or 'wipe_in')
    :param specific_slat_translate_distances: The distance each slat will move if using the translate system.
    This should be in a dictionary format - not all slat needs to have the distance, only those that will be different
    from the default value of 2.
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

    # prepares materials for each slat.  If the translate animation is used,
    # a different material for each entry group needs to be created
    materials = {}
    if animation_type == 'translate' and animate_slat_group_dict is not None:
        for key, value in animate_slat_group_dict.items():
            if value not in materials:
                layer_id = slats[key].layer
                color = mpl.colormaps[colormap].colors[layer_id-1]
                materials[value] = create_slat_material(color + (1,), f'Material Group {value}, Layer{layer_id}', alpha_animation=True)
    else:
        num_materials = slat_array.shape[2]
        for i in range(num_materials):
            color = mpl.colormaps[colormap].colors[i]
            materials[i+1] = create_slat_material(color + (1,), f'Layer {i + 1}', alpha_animation=False)

    # prepares variables
    cylinder_min_boundaries = [np.inf, np.inf, np.inf]
    cylinder_max_boundaries = [0, 0, 0]
    max_frame = 0

    if seed_layer_and_array is not None:
        seed_material = create_slat_material((1, 0, 0) + (1,), f'Seed Material')
        interpret_seed_system(seed_layer_and_array, seed_material, seed_length=list(slats.values())[0].max_length/2,
                              grid_xd=grid_xd, grid_yd=grid_yd)

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
        if animation_type != 'translate':
            bpy.context.object.data.materials.append(materials[layer])
        elif animation_type == 'translate' and animate_slat_group_dict is not None:
            bpy.context.object.data.materials.append(materials[animate_slat_group_dict[slat_id]])

        if animate_slat_group_dict is not None:
            frame_start = animate_slat_group_dict[slat_id] * animate_delay_frames
            if frame_start == 0:
                frame_start = 1
            frame_end = frame_start + animate_delay_frames
            max_frame = max(max_frame, frame_end)  # tracks the maximum amount of frames in the animation
            if animation_type == 'wipe_in':
                set_slat_wipe_in_animation(frame_start, frame_end, slat_id, cylinder, center, rotation, length, hide_cube=True)
            elif animation_type == 'translate':
                if specific_slat_translate_distances is not None and slat_id in specific_slat_translate_distances:
                    translate_distance = specific_slat_translate_distances[slat_id]
                else:
                    translate_distance = 2
                set_slat_translate_animation(frame_start, frame_end, cylinder, center, rotation, length, translate_distance)
            else:
                raise RuntimeError('Animation type not recognized.')

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

    # setting up transparent background for quicker setup
    render_settings = bpy.context.scene.render
    render_settings.film_transparent = True

    # Ensures the view mode is updated
    bpy.context.view_layer.update()

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(save_folder, '3D_blender_view.blend'))

