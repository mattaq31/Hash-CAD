## Developer Installation

To install the python interface and allow for changes to the code to be immediately updated in your package, clone the main git repository and navigate to the `crisscross_kit` directory. Next, run:

```bash
pip install -e .
```

You may also choose to install the package dependencies using other package managers, such as conda. The requirements are listed in `requirements.txt`.

- To install with pip run the following: `pip install -r requirements.txt`
- For conda run the following: `conda install -c conda-forge --file requirements.txt`
- For [PyVista](https://pyvista.org), install the dependencies from `requirements_pyvista.txt`.
- For [Blender](https://www.blender.org), simply run `pip install bpy`

## Useful locations

The `crisscross_kit/crisscross/scripts` directory contains various scripts the team has used for testing or creating different megastructure designs, which can be used as a basis for any new design.

The `crisscross_kit/crisscross/dna_source_plates` directory contains various source plates used by the crisscross team.  These layouts can be adopted or adjusted as necessary.

## File Formats

### Design File (.xlsx)

Designs are stored as Excel files with these worksheets:

| Worksheet          | Contents                                                          |
|--------------------|-------------------------------------------------------------------|
| slat_layer_x       | Slat positions on layer x                                         |
| handle_interface_x | Assembly handles between layer x and layer x + 1                  |
| cargo_layer_x_y_z  | Cargo tags placed on layer x, where y/z are lower/upper and h2/h5 |
| seed__layer_x_y_z  | Placement of seed handles.  Syntax identical to that of cargo.    |
| metadata           | Layer colours, slat counts, etc.                                  |
| slat_types         | Slat type for each slat placed in the design.                     |
| slat_handle_links  | Any links enforced between different handles in the design.       |

### Source Plate File (.xlsx)

DNA source plates follow this format:

| Column        | Description                               |
|---------------|-------------------------------------------|
| well          | Plate position (A1, A2, ...)              |
| name          | Handle identifier (see naming convention) |
| sequence      | DNA sequence                              |
| description   | Optional descriptor                       |
| concentration | Staple concentration (in uM)              |

**Naming convention**: `CATEGORY-VALUE-hSIDE-position_SLATPOS`

Examples:
- `ASSEMBLY_HANDLE-1-h2-position_1`
- `CARGO-marker-h5-position_16`
- `FLAT-none-h2-position_1`

## Building for PyPI

For developers looking to build the package for PyPI, you can use the following commands from the `crisscross_kit` directory of the repository:

First, make sure the build tools are installed:
```bash
pip install build twine setuptools-scm
```

Next, build the package:
```bash
python -m build
```

The build command will create a `dist` folder containing the `.whl` and `.tar.gz` files for the package. These can be uploaded to PyPI using:
```bash
twine upload dist/*
```

You will need to have a PyPI account and set up your credentials in `~/.pypirc` for the upload to work (you will also need to be set as a collaborator on the `crisscross_kit` project too).


## Local Docs Generation

The documentation available here is built using [mkdocs](https://www.mkdocs.org/).  You can build a local version of the docs using the following commands from the `docs` directory:

```bash
mkdocs build

mkdocs serve
```
You can then view the docs from `http://127.0.0.1:8000/` for quick debugging.

## GitHub Actions

Building and releasing all packages to PyPi is automated using a GitHub actions workflow (```.github/workflows/deploy_crisscross_kit_to_pypi.yml```). Briefly, this workflow builds the package for all operating systems (including the C code for ```eqcorr2d```) and uploads the resulting wheels to PyPi.  The same workflow can be emulated locally if necessary.

The workflow is triggered automatically when a new tag with format 'python-x.y.z' is pushed to the repository on the main branch.

---

