# TODO: This file is still a work-in-progress
import importlib
from colorama import Fore
import os
import matplotlib as mpl
import shutil

from crisscross.core_functions.slats import convert_slat_array_into_slat_objects
from crisscross.helper_functions.slat_salient_quantities import connection_angles, slat_width

bpy_spec = importlib.util.find_spec("bpy")  # only imports bpy if this is available
if bpy_spec is not None:
    import bpy
    import mathutils
    blender_bin = shutil.which("Blender")
    if blender_bin:
        bpy.app.binary_path = blender_bin
    else:
        print("Unable to find blender!")
    bpy_available = True
else:
    bpy_available = False
    print('The Blender API is not installed.  3D graphical views cannot be created using Blender.')


# Function to point an object at a target
def look_at(obj, target):
    direction = target - obj.location
    rot_quat = direction.to_track_quat('Z', 'Y')
    obj.rotation_euler = rot_quat.to_euler()


def create_emission_shader(color, strength, mat_name):
    # create a new material resource (with its associated shader)
    mat = bpy.data.materials.new(mat_name)
    # enable the node-graph edition mode
    mat.use_nodes = True

    # clear all starter nodes
    nodes = mat.node_tree.nodes
    nodes.clear()

    # add the Emission node
    node_emission = nodes.new(type="ShaderNodeEmission")
    node_emission.location = 0, 0
    # (input[0] is the color)
    node_emission.inputs[0].default_value = color
    # (input[1] is the strength)
    node_emission.inputs[1].default_value = strength

    # add the Output node
    node_output = nodes.new(type="ShaderNodeOutputMaterial")
    node_output.location = 100, 0

    # link the two nodes
    links = mat.node_tree.links
    link = links.new(node_emission.outputs[0], node_output.inputs[0])

    # return the material reference
    return mat


def create_slat_material(color, mat_name, metallic_strength=0.3):
    # Create a new material
    material = bpy.data.materials.new(name=mat_name)

    # Enable 'Use Nodes'
    material.use_nodes = True

    # Get the material's node tree
    nodes = material.node_tree.nodes

    # Clear all nodes to start fresh
    for node in nodes:
        nodes.remove(node)

    # Add a Principled BSDF shader node
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)

    # Assign a base color using an RGB code
    bsdf.inputs['Base Color'].default_value = color

    # Set metallic value
    bsdf.inputs['Metallic'].default_value = metallic_strength  # Slightly metallic

    # Add an Output node
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)

    # Connect BSDF shader to Output node
    material.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return material


def create_graphical_3D_view_bpy(slat_array, save_folder, slats=None, animate_slat_group_dict=None, animate_delay_frames=20,
                                 connection_angle='90', colormap='Set1'):
    """
    Creates a 3D video of a megastructure slat design. TODO: add cargo and seeds to this view too.
    :param slat_array: A 3D numpy array with x/y slat positions (slat ID placed in each position occupied)
    :param save_folder: Folder to save all video to.
    :param slats: Dictionary of slat objects (if not provided, will be generated from slat_array)
    :param connection_angle: The angle of the slats in the design (either '90' or '60' for now).
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

    shaders = []
    materials = []
    for i in range(slat_array.shape[2]):
        color = mpl.colormaps[colormap].colors[i]
        shaders.append(create_emission_shader(color + (1,), 0.5, f'Layer {i + 1}'))
        materials.append(create_slat_material(color + (1,), f'Layer {i + 1}'))

    for slat_num, (slat_id, slat) in enumerate(slats.items()):  # Z-height is set to 1 here, could be interested in changing in some cases

        pos1 = slat.slat_position_to_coordinate[1]
        pos2 = slat.slat_position_to_coordinate[32]
        layer = slat.layer
        length = slat.max_length

        start_point = (pos1[1] * grid_xd, pos1[0] * grid_yd, layer - 1)
        end_point = (pos2[1] * grid_xd, pos2[0] * grid_yd, layer - 1)

        # Calculate the center and direction from start and end points
        center = ((start_point[0] + end_point[0]) / 2, (start_point[1] + end_point[1]) / 2, layer - 1)

        point1 = mathutils.Vector(start_point)
        point2 = mathutils.Vector(end_point)

        direction = (point2 - point1).normalized()
        up = mathutils.Vector((0, 0, 1))
        rotation = up.rotation_difference(direction).to_euler()

        # Create the cylinder
        obj = bpy.ops.mesh.primitive_cylinder_add(
            location=center,
            radius=slat_width/2,
            rotation=rotation,
            depth=length
        )
        bpy.context.object.name = slat_id
        bpy.ops.object.shade_smooth()
        bpy.context.object.data.materials.append(materials[layer - 1])  # TODO: how would I add the emission to this material?

        if animate_slat_group_dict is not None:
            # Set initial visibility to False
            bpy.context.object.hide_viewport = True
            bpy.context.object.keyframe_insert(data_path="hide_viewport", frame=0)

            # Set visibility to True in the next frame
            bpy.context.object.hide_viewport = False
            bpy.context.object.keyframe_insert(data_path="hide_viewport", frame=animate_slat_group_dict[slat_id] * animate_delay_frames)

    # Create an area light
    bpy.ops.object.light_add(type='AREA', location=(5, -5, 5))
    area_light = bpy.context.object
    area_light.name = "Area Light"
    area_light.data.energy = 1000

    # Point the area light at the center
    look_at(area_light, mathutils.Vector((0, 0, 0)))

    # Create a camera
    bpy.ops.object.camera_add(location=(10, -10, 10))
    camera = bpy.context.object
    camera.name = "Camera"

    # Point the camera at the center
    look_at(camera, mathutils.Vector((0, 0, 0)))

    # Set the camera as the active camera
    bpy.context.scene.camera = camera

    # Save the Blender file
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(save_folder, '3D_blender_view.blend'))
