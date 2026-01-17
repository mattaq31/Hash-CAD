## What can #-CAD do?

\#-CAD is meant as the one-stop solution for designing and optimizing a DNA megastructure design.  The key features include:

- **Visual Design**: An intuitive 2D grid interface for designing megastructure slat layouts and handle binding positions
- **Handle Optimization**: Evolutionary algorithm for optimizing assembly handle sequences to minimize parasitic interactions
- **3D Visualization**: Real-time 3D rendering of your designs
- **Echo Export**: Direct export to Echo Liquid Handler command sheets
- **Python Integration**: Seamless integration with the `crisscross-kit` Python library

## Quick Guide

### The Main Interface

The user interface is divided into three zones:

1. **2D Grid View** (left): The primary design canvas where you place and edit slats, handles and cargo tags
2. **3D View** (right): 3D visualization of design.  This can be interacted with independently of the 2D grid, but edits cannot be made to the actual design from this panel.
3. **Sidebar** (far-left): Context-sensitive panels that provide tools for adding, modifying or deleting slats, handles and cargo.

### Design Modes

Several different design editing modes are available via the sidebar:

| Mode | Description                                        |
|------|----------------------------------------------------|
| **Slat Design** | Add, remove, and edit slats on the grid            |
| **Assembly Handles** | Assign, edit and optimize assembly handles         |
| **Cargo & Seed** | Place and edit cargo molecules and seed structures |
| **Echo Config** | Configure Echo Liquid Handler export settings      |

### Basic Workflow

1. **Create or load a design**: Start with a new design or import an existing `.xlsx` file
2. **Design your slat layout**: Place slats on the 2D grid to form your megastructure, taking care to ensure slats criscross on different layers
3. **Optimize assembly handles**: Run the evolutionary algorithm to find optimal handle sequences
4. **Add cargo and seeds**: Place functional elements on your design
5. **Export**: Generate Echo commands or save your design for Python processing

## Next Steps

- [Installation](installation.md) - Download and install #-CAD
- [Slat Design](slat-design.md) - Learn how to use the 2D grid design interface
- [Assembly Handles](assembly-handles.md) - Apply the evolutionary algorithm to minimize parasitic interactions
- [Cargo & Seeds](cargo-seeds.md) - Attach seeds and functional cargo tags
- [Exporting to an Echo Liquid Handler](echo-export.md) - Export your design for lab assembly
