# Crisscross Design Library Usage Guide 
The `crisscross` library is a python-importable package that can:
- Import and edit megastructures from #-CAD files.
- Evolve assembly handles using a customized evolutionary algorithm.
- Assign cargo and seed handles to a megastructure, as well as implement customized edits.
- Export a megastructure to an Echo Liquid Handler command sheet.
- Generate experiment helper sheets to aid large-scale laboratory assembly and purification.
- Generate graphics for a megastructure, including 2D schematics, 3D models and Blender animations.
- Provide a number of other utility functions for resuspending plates, organizing handle libraries and more.

The below provides a brief guide and examples on how to use this library alongside #-CAD.  For more detailed documentation, please refer to the code itself, which is well commented and provides examples of how to use each class and function.

## Importing and Editing a Megastructure
- The file format is identical to that of #-CAD i.e. all info is stored within an Excel file.  The file information should be passed to the `Megastructure` class, which is the main container for a design.  To import a megastructure designed in #-CAD, simply run:

```python
from crisscross.core_functions import Megastructure

megastructure = Megastructure(import_design_file="path/to/excel_sheet.xlsx")
```
Alternatively, a megastructure can be built from a slat bundle, which is a 3D numpy array with format `(x, y, layer)`, where `x` and `y` are the dimensions of the slat bundle and `layer` is the layer number.  Within the array, each slat should have a unique ID per layer, and 32 positions should be occupied per slat.  For example (also available [here](https://github.com/mattaq31/Crisscross-Design/blob/main/crisscross_kit/crisscross/core_functions/slat_design.py#L10)):
```python
import numpy as np

def generate_standard_square_slats(slat_count=32):
    """
    Generates a base array for a square megastructure design
    :param slat_count: Number of handle positions in each slat
    :return: 3D numpy array with x/y slat positions and a list of the unique slat IDs for each layer
    """
    base_array = np.zeros((slat_count, slat_count, 2))  # width, height, X/Y slat ID

    for i in range(1, slat_count+1):  # slats are 1-indexed and must be connected
        base_array[:, i-1, 1] = i
        base_array[i-1, :, 0] = i

    unique_slats_per_layer = []
    for i in range(base_array.shape[2]):
        slat_ids = np.unique(base_array[:, :, i])
        slat_ids = slat_ids[slat_ids != 0]
        unique_slats_per_layer.append(slat_ids)

    return base_array, unique_slats_per_layer
```
With a slat array defined, this can be passed to the `Megastructure` class as follows:

```python
from crisscross.core_functions import Megastructure
from crisscross.core_functions import generate_standard_square_slats

slat_array, _ = generate_standard_square_slats()
megastructure = Megastructure(slat_array)
```
The `Megastructure` class will then create a dictionary of `Slat` objects, which can be accessed via the `slats` attribute.  Each `Slat` object contains information about the slat's handles and position.  

If your design file contains assembly, cargo or seed handles, these will all be imported into the megastructure class.  'Placeholder' values are assigned for all handles until you provide sourec plates (see below).

Other customization options are available, which are described in the class` [documentation](https://github.com/mattaq31/Hash-CAD/blob/main/crisscross_kit/crisscross/core_functions/megastructures.py).

## Assembly Handle Evolution

Optimizing assembly handles for a design can be taken care of by our customized evolutionary algorithm.  In brief, the algorithm starts from an initial guess and then randomly mutates a set of handles.  The mutated designs are then evaluated through both a hamming and physics-based score, and the best designs are retained for subsequent mutations.  This loop is repeated until some stopping criterion is met.

Evolution is handled by the `EvolveManager` [class](https://github.com/mattaq31/Crisscross-Design/blob/main/crisscross_kit/crisscross/assembly_handle_optimization/handle_evolution.py), for which documentation is provided in the code itself.  An example of how to use the class is provided [here](https://github.com/mattaq31/Crisscross-Design/blob/main/crisscross_kit/scripts/assembly_handle_optimization/debugging_evolution.py). The scripting system can be set to be multi-threaded, which should improve performance.  Due to the vectorized implementation used to calculate the hamming distance, the algorithm can significantly slow down with very large arrays (we are looking into this).

A CLI function is also provided to allow evolution to be carried out easily on server clusters.  To use the CLI, simply run:
```bash
handle_evolve -c config_file.toml
```
The config file accepts the same options available in the main `EvolveManager` class.  An example config file is available below (the handle array can be used directly from a saved design file):
```toml
early_hamming_stop = 31
evolution_generations = 20000
evolution_population = 800
process_count = 18
generational_survivors = 5
mutation_rate = 2
slat_length = 32
unique_handle_sequences = 32
split_sequence_handles = true
mutation_type_probabilities = [ 0.425, 0.425, 0.15,]
progress_bar_update_iterations = 10
random_seed = 8
mutation_memory_system = "off"
log_tracking_directory = "/path_to_experiment_directory"
slat_array = "/path/to/design_file.xlsx"
```
## Assigning Cargo
If assigning cargo programmatically, simply prepare a numpy array of the same size as your slat array (filled with zeros).  Cargo positions should be indicated in the array with a unique integer for each cargo type.  The array can then be assigned to a megastructure as follows:
```python
megastructure.assign_cargo_handles_with_array(cargo_array, cargo_key={1: 'antiBart', 2: 'antiEdna'}, layer='top')
```
The above commands assign cargo to the top layer of a megastructure.  All 1s are assigned the tag `antiBart` and all 2s are assigned the tag `antiEdna`.  These keys are important as they will be used in subsequent steps when extracting sequences from source plates.  As before, full documentation on customization options is available within the `Megastructure` class code.

## Assigning a Seed
Assigning a seed to a megastructure is more complex than cargo and it is recommended to use #-CAD to properly place a seed in your design.  However, you may also do this programmatically by preparing a dictionary:
- The keys should be of form `(seed_id, layer, side)` e.g. `('A', 1, 5)`.
- For each key, you should provide a list of tuples, where each tuple contains the x and y coordinates of the seed handle, as well as the handle ID (one of `1_1`, `1_2`,..., `5_16`).
You can then assign the seed to your megastructure as follows:
```python
megastructure.assign_seed_handles(seed_dict)
```
- A #-CAD export file of a design that includes a seed should already have this information available. 

## Plates, Exporting to Echo Liquid Handler and Experiment Helpers

Once a design is completed, a megastructure can be exported directly to an [Echo Liquid Handler](https://www.beckman.com/liquid-handlers/echo-acoustic-technology) command sheet.  You will first need to provide a set of DNA plates containing your source H2/H5 handles for each component in your design.  For the crisscross development team, our handle plates are stored [here](https://github.com/mattaq31/Hash-CAD/tree/main/dna_source_plates).  You could use these same plates, or purchase your own sets.  If you do purchase your own set, you will need to prepare excel sheets that follow the same format as those in the `dna_source_plates` folder. The most important part of the formatting system is that each sequence is provided a name that is encoded as follows:

`CATEGORY-VALUE-hSIDE-position_SLATPOS` e.g. `CARGO-antiBart-h5-position_5`

The available categories are: `CARGO`, `SEED`, `ASSEMBLY_HANDLE`, `ASSEMBLY_ANTIHANDLE` & `FLAT` (i.e. no handle jutting out of the slat).

Once your plates have been defined and loaded into the crisscross library, you can assign sequences/wells to all handles in your design as follows:

```python
from crisscross.plate_mapping import get_cutting_edge_plates, get_cargo_plates

main_plates = get_cutting_edge_plates()
cargo_plates = get_cargo_plates()

megastructure.patch_placeholder_handles(main_plates + cargo_plates)
megastructure.patch_flat_staples(main_plates[0]) # this plate contains only flat staples
```
Plates can have multiple identical wells, from which the Echo will attempt to draw liquid according to their fill level.

With all handles assigned, the megastructure can be exported to an Echo command sheet as follows:

```python
from crisscross.core_functions import convert_slats_into_echo_commands

echo_sheet = convert_slats_into_echo_commands(slat_dict=megastructure.slats,
                                              destination_plate_name='plate_name',
                                              reference_transfer_volume_nl=75,
                                              # base liquid transfer volume for one staple at the reference concentration
                                              reference_concentration_uM=500,  # reference concentration for one staple
                                              output_folder='path_to_folder',
                                              center_only_well_pattern=False,
                                              # set to true to only use the center wells of the output plate
                                              plate_viz_type='barcode',
                                              normalize_volumes=True,
                                              # set to true to normalize the volumes of each output well (by adding extra buffer or water to wells that have low volumes)
                                              output_filename='echo_commands.csv')
```
For more info and customization options, refer to the in-line documentation [here](https://github.com/mattaq31/Crisscross-Design/blob/main/crisscross_kit/crisscross/core_functions/megastructure_composition.py#L198).

After mixing your megastructure slat handles, you will next need to anneal and purify each slat before megastructure formation.  Experiment helpers to guide this process can also be generated from the megastructure class data as follows (docs available [here](https://github.com/mattaq31/Hash-CAD/blob/main/crisscross_kit/crisscross/helper_functions/lab_helper_sheet_generation.py#L462)):
```python
from crisscross.helper_functions.lab_helper_sheet_generation import prepare_all_standard_sheets

prepare_all_standard_sheets(megastructure.slats, 'output_file_name.xlsx',
                            reference_single_handle_volume=75,
                            reference_single_handle_concentration=500,
                            echo_sheet=echo_sheet, # previously generated via the echo command
                            handle_mix_ratio=15, # setting to 15 as a buffer, technically only 10x handle:scaffold is required
                            peg_concentration=3, # set to the concentration of PEG solution you have in stock
                            peg_groups_per_layer=4 # splits a layer into 4 different PEG groups)
```
- Further details and options are available in the documentation for each function.
## Graphics Generation
The Python API also allows you to automatically generate various graphics linked to your megastructure design.  These include 2D schematics for each slat layer, an x-ray view of your design, 2D schematics of your assembly handles, a spinning 3D model video (requires `pyvista`) and a blender file (requires `bpy`) which can be configured with an animation showing the expected crisscross assembly process.  An example of how to generate these files for a typical design is provided below:
```python
megastructure.create_standard_graphical_report('output_folder', generate_3d_video=True)
megastructure.create_blender_3D_view('output_folder', camera_spin=False, animate_assembly=True, animation_type='translate', correct_slat_entrance_direction=True, include_bottom_light=False)
```
- The blender animation might require hand-correction to select the correct slat order (this depends on how complex your design is).

For further info on customization options, check out the related functions in the `Megastructure` class.

Example graphics generated from the hexagram design are provided below (low-resolution versions):
<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/hexagram_low_res_images/3D_design_view.gif" alt="hexagram_gif" style="width: 30%; margin: 0.5%;">
</p>
<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/hexagram_low_res_images/global_view.jpeg" alt="hexagram X-ray view" style="width: 40%; margin: 0.5%;">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/hexagram_low_res_images/handles_layer_1_2.jpeg" alt="hexagram handles" style="width: 40%; margin: 0.5%;">
</p>
<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/hexagram_low_res_images/layer_1_hexagram.jpeg" alt="hexagram layer 1" style="width: 40%; margin: 0.5%;">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/hexagram_low_res_images/layer_2_hexagram.jpeg" alt="hexagram layer 2" style="width: 40%; margin: 0.5%;">
</p>

## Building for PyPI
- For developers looking to build the package for PyPI, you can use the following commands from the `crisscross_kit` directory of the repository:
- First, make sure the build tools are installed:
```bash
pip install build twine setuptools-scm
```
- Next, build the package:
```bash
python -m build
```
- The build command will create a `dist` folder containing the `.whl` and `.tar.gz` files for the package. These can be uploaded to PyPI using:
```bash
twine upload dist/*
```
- You will need to have a PyPI account and set up your credentials in `~/.pypirc` for the upload to work (you will also need to be set as a collaborator on the `crisscross_kit` project too).
