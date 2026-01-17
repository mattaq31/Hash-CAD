# Crisscross Kit Python Library

  The `crisscross` python API can be used to manipulate megastructures programmatically, and its file format is fully compatible with that of #-CAD. The Python interface provides more flexibility and customizability when compared to #-CAD, at the cost of a steeper learning curve.

## Installation and Requirements

The Python package was developed using Python 3.11. Other versions of Python should also work, but it is recommended to use 3.10+.

To install the python interface, simply run the below in your environment of choice:

```bash
pip install crisscross_kit
```

(Optional) If you would like to be able to generate 3D graphics or 3D blender files for further customization, you need to install additional dependencies:

```bash
pip install crisscross_kit[3d]
pip install crisscross_kit[blender]
```

---
## Quick Start Guide

The `crisscross` library is a python-importable package that can:

- Import and edit megastructures from #-CAD files.
- Evolve assembly handles using a customized evolutionary algorithm.
- Assign cargo and seed handles to a megastructure, as well as implement customized edits.
- Export a megastructure to an Echo Liquid Handler command sheet.
- Generate experiment helper sheets to aid large-scale laboratory assembly and purification.
- Generate graphics for a megastructure, including 2D schematics, 3D models and Blender animations.
- Provide a number of other utility functions for resuspending plates, organizing handle libraries and more.

The below provides a brief guide and examples on how to use this library alongside #-CAD. For more detailed documentation, please refer to the code itself, which is well commented and provides examples of how to use each class and function.

### Importing and Editing a Megastructure

The file format is identical to that of #-CAD i.e. all info is stored within an Excel file. The file information should be passed to the `Megastructure` class, which is the main container for a design. To import a megastructure designed in #-CAD, simply run:

```python
from crisscross.core_functions.megastructures import Megastructure

megastructure = Megastructure(import_design_file="path/to/excel_sheet.xlsx")
```

Alternatively, a megastructure can be built from a slat bundle, which is a 3D numpy array with format `(x, y, layer)`, where `x` and `y` are the dimensions of the slat bundle and `layer` is the layer number. Within the array, each slat should have a unique ID per layer, and 32 positions should be occupied per slat.

```python
from crisscross.core_functions.megastructures import Megastructure
from crisscross.core_functions.slat_design import generate_standard_square_slats

slat_array, _ = generate_standard_square_slats()
megastructure = Megastructure(slat_array)
```

The `Megastructure` class will then create a dictionary of `Slat` objects, which can be accessed via the `slats` attribute. Each `Slat` object contains information about the slat's handles and position.

If your design file contains assembly, cargo or seed handles, these will all be imported into the megastructure class. 'Placeholder' values are assigned for all handles until you provide source plates (see below).

### Assigning Cargo

If assigning cargo programmatically, simply prepare a numpy array of the same size as your slat array (filled with zeros). Cargo positions should be indicated in the array with a unique integer for each cargo type. The array can then be assigned to a megastructure as follows:

```python
megastructure.assign_cargo_handles_with_array(cargo_array, cargo_key={1: 'antiBart', 2: 'antiEdna'}, layer='top')
```

The above commands assign cargo to the top layer of a megastructure. All 1s are assigned the tag `antiBart` and all 2s are assigned the tag `antiEdna`. These keys are important as they will be used in subsequent steps when extracting sequences from source plates.

### Assigning a Seed

Assigning a seed to a megastructure is more complex than cargo and it is recommended to use #-CAD to properly place a seed in your design. However, you may also do this programmatically by preparing a dictionary:

- The keys should be of form `(seed_id, layer, side)` e.g. `('A', 1, 5)`.
- For each key, you should provide a list of tuples, where each tuple contains the x and y coordinates of the seed handle, as well as the handle ID (one of `1_1`, `1_2`,..., `5_16`).

You can then assign the seed to your megastructure as follows:

```python
megastructure.assign_seed_handles(seed_dict)
```

A #-CAD export file of a design that includes a seed should already have this information available.

### Plates, Exporting to Echo Liquid Handler and Experiment Helpers

Once a design is completed, a megastructure can be exported directly to an [Echo Liquid Handler](https://www.beckman.com/liquid-handlers/echo-acoustic-technology) command sheet. You will first need to provide a set of DNA plates containing your source H2/H5 handles for each component in your design.

For the crisscross development team, our handle plates are stored [here](https://github.com/mattaq31/Hash-CAD/tree/main/crisscross_kit/crisscross/dna_source_plates). You could use these same plates, or purchase your own sets. If you do purchase your own set, you will need to prepare excel sheets that follow the same format as those in the `dna_source_plates` folder.

Once your plates have been defined and loaded into the crisscross library, you can assign sequences/wells to all handles in your design as follows:

```python
from crisscross.plate_mapping import get_cutting_edge_plates, get_cargo_plates

main_plates = get_cutting_edge_plates()
cargo_plates = get_cargo_plates()

megastructure.patch_placeholder_handles(main_plates + cargo_plates)
megastructure.patch_flat_staples(main_plates[0])  # this plate contains only flat staples
```

With all handles assigned, the megastructure can be exported to an Echo command sheet as follows:

```python
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands

echo_sheet = convert_slats_into_echo_commands(
    slat_dict=megastructure.slats,
    destination_plate_name='plate_name',
    reference_transfer_volume_nl=75,
    reference_concentration_uM=500,
    output_folder='path_to_folder',
    center_only_well_pattern=False,
    plate_viz_type='barcode',
    normalize_volumes=True,
    output_filename='echo_commands.csv'
)
```

Various other Echo export options are available (see the code for more details).

### Graphics Generation

The Python API also allows you to automatically generate various graphics linked to your megastructure design. These include 2D schematics for each slat layer, an x-ray view of your design, 2D schematics of your assembly handles, a spinning 3D model video (requires `pyvista`) and a blender file (requires `bpy`).

```python
megastructure.create_standard_graphical_report('output_folder', generate_3d_video=True)

megastructure.create_blender_3D_view(
    'output_folder',
    camera_spin=False,
    animate_assembly=True,
    animation_type='translate',
    correct_slat_entrance_direction=True,
    include_bottom_light=False
)
```

Example graphics generated from the hexagram design:

<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/hexagram_low_res_images/3D_design_view.gif" alt="hexagram_gif" style="margin: 0.5%;">
</p>
<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/hexagram_low_res_images/global_view.jpeg" alt="hexagram X-ray view" style="width: 40%; margin: 0.5%;">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/hexagram_low_res_images/handles_layer_1_2.jpeg" alt="hexagram handles" style="width: 40%; margin: 0.5%;">
</p>

---

`!!! quote "Citation"
    If you use the Crisscross Python Kit or #-CAD in your research, please cite our work (details coming out soon).
`
