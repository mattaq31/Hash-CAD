# Crisscross Kit Python Library

[![PyPI version](https://img.shields.io/pypi/v/crisscross_kit.svg)](https://pypi.org/project/crisscross_kit/)
[![Documentation](https://img.shields.io/badge/docs-Read%20the%20Docs-blue)](https://hash-cad.readthedocs.io/python-api/)

Python library for DNA megastructure design, complementing the #-CAD desktop application. Provides programmatic access to design manipulation, handle evolution, and Echo Liquid Handler export.

## Installation

```bash
pip install crisscross_kit
```

Optional dependencies for 3D graphics and Blender:
```bash
pip install crisscross_kit[3d]
pip install crisscross_kit[blender]
```

For the orthogonal sequence generator (`orthoseq_generator`), you'll also need [NUPACK 4.x](https://www.nupack.org/download/overview).

## Quick Example

```python
from crisscross.core_functions import Megastructure

# Load a design created in #-CAD
mega = Megastructure(import_design_file="my_design.xlsx")

# Access slat data
print(f"Design has {len(mega.slats)} slats")

# Generate graphics
mega.create_standard_graphical_report('output_folder/')
```

## Documentation

**Full documentation**: [https://hash-cad.readthedocs.io/](https://hash-cad.readthedocs.io/python-api/)

## Developer Installation

Clone and install in editable mode:

```bash
git clone https://github.com/mattaq31/Hash-CAD.git
cd Hash-CAD/crisscross_kit
pip install -e .
```

## License

MIT License - see [LICENSE](../LICENSE) for details.
