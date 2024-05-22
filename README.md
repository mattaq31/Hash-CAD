# Crisscross-Design

Collection of scripts and packages for working on crisscross origami.  More details and updates TBC.

To install, navigate to the root directory and run:

`pip install -e .`

Separate packages required (install via conda):
- numpy
- pandas
- matplotlib
- openpyxl
- tqdm

Best place to start is `scripts/optical_computing_collab/square_design_for_optical_computers.py`

For the glider design, navigate to `scripts/gliders/glider_design.py`, and to convert the design to an echo csv file, navigate to `scripts/gliders/glider_megastructure_creation.py`.  You will need to update filepaths to match your system.

All defined plates are located in the `core_plates` and `cargo_plates` directories.

