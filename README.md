# #-CAD and Crisscross Library Packages

<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/media_kit/basic_logo.png" alt="Hash-CAD in action" style="width: 50%; margin: 0%;">
</p>
<p align="center">
  <em>Unified CAD and scripting packages for megastructure design, handle library generation and visualization.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows%20%7C%20Web-blue" alt="Platform Support">
  <a href="https://github.com/mattaq31/Hash-CAD/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT">
  </a>
</p>

<p align="center">
<a href="https://pypi.org/project/crisscross_kit/">
  <img src="https://img.shields.io/pypi/v/crisscross_kit.svg?label=PyPI%20Crisscross%20Kit%20Latest&logo=python&logoColor=white">
</a>
  <a href="https://pypi.org/project/crisscross_kit/">
    <img src="https://img.shields.io/pypi/dm/crisscross_kit.svg?label=PyPI%20downloads&logo=python&logoColor=white">
  </a>
<a href="https://hash-cad.readthedocs.io/en/latest/">
  <img src="https://img.shields.io/badge/docs-Read%20the%20Docs-8CA1AF.svg?style=flat&logo=python&logoColor=white">
</a>
</p>

<p align="center">
<a href="https://github.com/mattaq31/Hash-CAD/releases">
  <img src="https://img.shields.io/github/v/tag/mattaq31/Hash-CAD?label=%23-CAD%20Latest&logo=flutter&logoColor=white&style=flat">
</a>
<a href="https://github.com/mattaq31/Hash-CAD/actions/workflows/flutter-web-deploy.yml">
  <img src="https://img.shields.io/github/actions/workflow/status/mattaq31/Hash-CAD/flutter-web-deploy.yml?label=Web&style=flat&logo=flutter&logoColor=white" alt="Web CI Status">
</a>
<a href="https://github.com/mattaq31/Hash-CAD/actions/workflows/flutter-test.yml">
  <img src="https://img.shields.io/github/actions/workflow/status/mattaq31/Hash-CAD/flutter-test.yml?branch=main&label=Tests&style=flat&logo=flutter&logoColor=white" alt="Flutter Tests Status">
</a>
  <img src="https://img.shields.io/github/downloads/mattaq31/Hash-CAD/total?label=Downloads&logo=flutter&logoColor=white&style=flat" alt="GitHub all releases">
</p>

<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/bird_edit.png" alt="Hash-CAD in action" style="width: 80%; margin: 0.5%;">
</p>
<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/megastar_edit.png" alt="Hash-CAD in action" style="width: 80%; margin: 0.5%;">
</p>

## \#-CAD

\#-CAD provides a graphical interface for designing crisscross megastructures with features including:

- **2D Grid Design**: Intuitive slat placement on square or hexagonal grids
- **Handle Optimization**: Evolutionary algorithm for optimal assembly handle sequence selection from a finite library
- **3D Visualization**: Real-time 3D rendering of a design
- **Cargo and Seed Placement**: Free-form editing of cargo handle placement
- **Handle Linking**: The ability to link handles or generate duplicates to build repeating unit designs
- **Echo Export**: Direct export to Echo Liquid Handler command sheets
- **(Experimental) Double-Barrel slats** - The ability to design and optimize megastructures using double-barrel 2x16 slats (alongside the standard 1x32 slats) 

For comprehensive usage instructions, see the [User Guide](https://hash-cad.readthedocs.io/en/latest/user-guide/).

### Installation

**Desktop Application**: Download the latest release for your platform from [GitHub Releases](https://github.com/mattaq31/Hash-CAD/releases).

| Platform | Download                      |
|----------|-------------------------------|
| macOS | `Hash-CAD-macOS.zip`          |
| Windows | `Hash-CAD-windows.zip`  |
| Linux | `Hash-CAD-linux.tar.gz` |

**Web Application**: Simply open the application URL [here](https://www.hash-cad.com).

For detailed installation instructions, see the [Installation Guide](https://hash-cad.readthedocs.io/en/latest/user-guide/installation/).

Quick setup tutorial video also available [here](https://youtu.be/UYyZ-ENyqZ4)!

### TLDR Usage Guide

1. **Create or load a design**: Start fresh or import an existing `.xlsx` design file
2. **Design your slat layout**: Place slats on the 2D grid to form your megastructure.  Slats must crisscross each other on different layers to produce a valid design.
3. **Optimize handles**: Run the evolutionary algorithm to optimize handle sequence selection.
4. **Add cargo and seeds**: Place functional elements on your design and select the seed binding position (requires a total of 5x16 handles).
5. **Export**: Generate Echo commands or save for Python processing.

See the full [User Guide](https://hash-cad.readthedocs.io/en/latest/user-guide/) for more details.

## Crisscross Python API & Orthogonal Sequence Generation

  The `crisscross` python API can be used to manipulate megastructures programmatically, and its file format is fully compatible with that of #-CAD. The Python interface provides more flexibility and customizability when compared to #-CAD, at the cost of a steeper learning curve.

  The bundled `orthoseq_generator` package helps you find sets of **orthogonally binding DNA sequence pairs**. The main focus is on selecting sequences based on **thermodynamic binding energy**, not sequence diversity (as commonly used in barcoding).
### Installation

Simply install via pip (requires Python 3.11+):

```bash
pip install crisscross_kit
```

Please check our [docs](https://hash-cad.readthedocs.io/en/latest/) for more details on installation and usage of our joint python libraries for crisscross design and handle library orthogonal sequence generation.

## Development & Support
\#-CAD was developed in the [William Shih Lab](https://www.shih.hms.harvard.edu) at the Dana-Farber Cancer Institute and the Wyss Institute at Harvard University.  The following contributed to the codebase:

- [Matthew Aquilina](https://www.linkedin.com/in/matthewaq/) - Lead developer for the project.
- [Florian Katzmeier](mailto:florian_katzmeier@dfci.harvard.edu) - Developed handle assignment and handle library orthogonal sequence selection algorithms.
- [Stella (Siyuan) Wang](https://www.linkedin.com/in/siyuan-stella-wang-311936247/) - Developed initial megastructure assembly and hamming distance calculation protocols, and implemented various custom megastructure design systems in the final codebase.
- [Corey Becker](https://www.linkedin.com/in/corey-becker-b75656204/) - Developed initial prototype GUI using a combined javascript-python server and laid the foundation for the final #-CAD interface.

Experimental validation of #-CAD was carried out by the entire crisscross origami team, which also included:
- [Huangchen Cui](https://www.linkedin.com/in/huangchen-cui-642b33314/)
- [Yichen Zhao](https://www.linkedin.com/in/yichen-zhao-83410493/)
- [Minke Nijenhuis](https://www.linkedin.com/in/minkenijenhuis/)
- [Su Hyun Seok](https://www.linkedin.com/in/su-hyun-seok-10096755/)
- [Julie Finkel](https://www.linkedin.com/in/julie-finkel/)

All the above team members contributed to beta-testing and test-trialling the app during its development!

Development of the evolutionary algorithm was accelerated by the use of Harvard Medical School's O2 High Performance Compute Cluster.

This project was supported by various funding sources:

- A UK Medical Research Council Precision Medicine Transition Fellowship awarded to Matthew Aquilina (grant number MR/N013166/1)
- The Dana-Farber Cancer Institute's Claudia Adams Barr Program for Cancer Research 
- A Wyss Institute Northpond Alliance Director's Fund Award awarded to Matthew Aquilina
- The German Research Foundation (Deutsche Forschungsgemeinschaft, DFG) through the Walter Benjamin Programme (project number 553862611, awarded to Florian Katzmeier)
- The U.S. Department of Energy, Office of Science, Basic Energy Sciences, Biomolecular Materials Program (Award No. DE-SC0024136)
- The Carlsberg Foundation (grant CF23-1125, awarded to Minke Nijenhuis)
- A Sloan foundation grant (grant ID G-2021-16495)
- The Harvard College Research Program (funding Corey Becker)
- The Korea-US Collaborative Research Fund (KUCRF) funded by the Ministry of Science and ICT and Ministry of Health & Welfare, Republic of Korea (grant RS-2024-00468463)
- The Novo Nordisk Foundation (grant NNF23OC0084494)
- The Wyss Institute's Molecular Robotics Initiative 

For more details of everyone's coding contributions, please check the graphs [here](https://github.com/mattaq31/Hash-CAD/graphs/contributors). Contributions from the open-source community are welcome! 

## Literature Citation

Coming soon!

Accompanying data and a large set of examples is available at our Zenodo deposition [here](https://zenodo.org/records/17914052).

