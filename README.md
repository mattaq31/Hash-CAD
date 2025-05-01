# #-CAD

<p align="center">
  <img src="/graphics_screenshots/hexagram.png" alt="Hash-CAD in action" style="width: 47%; margin: 0.5%;">
  <img src="./graphics_screenshots/evolution.png" alt="Evolution Algorithm Usage" style="width: 47%; margin: 0.5%;">
</p>

<p align="center">
  <em>Unified CAD package for megastructure design, assembly and visualization.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-blue" alt="Platform Support">
  <a href="https://github.com/mattaq31/Hash-CAD/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT">
  </a>
  <img src="https://img.shields.io/github/downloads/mattaq31/Hash-CAD/total" alt="GitHub all releases">
</p>

## Main CAD Interface
### Installation
### Usage Guide

## Python API

### Installation and Requirements
- The Python package was developed using Python 3.11.  Other versions of Python should also work, but it is recommended to use 3.10+.
- To install the python interface, navigate to the root directory and run:

`pip install -e .`

- Next, install the package dependencies using your package manager of choice.  
  - For pip run the following: `pip install -r requirements.txt`
  - For conda run the following: `conda install -c conda-forge --file requirements.txt`
- (Optional), if you would like to be able to generate 3D graphics or 3D blender files for further customization, you need to install additional dependencies:
  - For [PyVista](https://pyvista.org), install the dependencies from `requirements_pyvista.txt` (either pip or conda).
  - For [Blender](https://www.blender.org), simply run `pip install bpy`
### Usage Guide

#### Importing and Editing a Megastructure

#### Exporting to Echo Liquid Handler

#### Graphics Generation

#### Assembly Handle Evolution

#### Handle Library Generation?

### #-CAD Bundled Python Server

## Development & Support
\#-CAD was developed in the [William Shih Lab](https://www.shih.hms.harvard.edu) at the Dana-Farber Cancer Institute and the Wyss Institute at Harvard University.  The following contributed to the codebase:

- [Matthew Aquilina](https://www.linkedin.com/in/matthewaq/) - Lead developer for the project.
- [Florian Katzmeier](mailto:florian_katzmeier@dfci.harvard.edu) - Developed handle assignment and handle library orthogonal sequence selection algorithms.
- [Stella (Siyuan) Wang](https://www.linkedin.com/in/siyuan-stella-wang-311936247/) - Developed initial megastructure assembly and hamming distance calculation protocols, and implemented various custom megastructure design systems in the final codebase.
- [Corey Becker](https://www.linkedin.com/in/corey-becker-b75656204/) - Developed initial prototype GUI using a combined javascript-python server and laid the foundation for the final #-CAD interface.

Experimental validation of #-CAD was carried out by the entire crisscross origami team, which also included [Huangchen Cui](https://www.linkedin.com/in/huangchen-cui-642b33314/), [Yichen Zhao](https://www.linkedin.com/in/yichen-zhao-83410493/) and [Minke Nijenhuis](https://www.linkedin.com/in/minkenijenhuis/).

For more details of everyone's coding contributions, please check the graphs [here](https://github.com/mattaq31/Hash-CAD/graphs/contributors).

Contributions from the open-source community are welcome!  In particular, we are looking for help with introducing unit tests to both the Python and Flutter packages!

Funding details TBC.

## Literature Citation
Coming soon!
