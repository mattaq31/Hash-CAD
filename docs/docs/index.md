<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/media_kit/basic_logo.png" alt="Hash-CAD Logo" width="300">
</p>

# Documentation for #-CAD and Python Libraries

This is the documentation for **#-CAD** (Hash-CAD), a unified CAD and scripting system for DNA megastructure (origami) design, handle library generation, and visualization, and various python libraries for manipulating DNA megastructures and generating orthogonal sequence libraries.

Developed in the [William Shih Lab](https://www.shih.hms.harvard.edu) at the Dana-Farber Cancer Institute and the Wyss Institute at Harvard.

---

## Getting Started

<div class="grid cards" markdown>

-   📘 **[User Guide](user-guide/index.md)**

    ---

    Learn how to install and use #-CAD.  Quick-access install instructions [here](user-guide/installation.md).

-   🐍 **[Crisscross Python Library](crisscross/index.md)**

    ---
    Programmatically manipulate megastructures, export to Echo, and generate graphics.

-   🧬 **[Orthoseq Generator](orthoseq/index.md)**

    ---

    Contribute to #-CAD's programming development.

-   🛠️ **[#-CAD Development](flutter-dev/index.md)**

    ---
    Generate orthogonal DNA sequence libraries for assembly handles using graph-based algorithms.

</div>

---

## Documentation Sections

### For Users

| Section | Description                                                                      |
|---------|----------------------------------------------------------------------------------|
| [User Guide](user-guide/index.md) | Desktop application tutorials, keyboard shortcuts, and workflow guides           |
| [Installation](user-guide/installation.md) | Download and install #-CAD and the python libraries for macOS, Windows, or Linux |

### Python Libraries

| Library                                 | Description |
|-----------------------------------------|-------------|
| [crisscross](crisscross/index.md)       | Core Python library for megastructure design, Echo export, and graphics |
| [orthoseq_generator](orthoseq/index.md) | Orthogonal sequence generation for assembly handle libraries |
| [eqcorr2d](eqcorr2d/index.md)           | High-performance C engine for computing parasitic valency matches |
| [API Reference](api-reference/index.md) | Complete Python API reference |

### For #-CAD Developers

| Section | Description |
|---------|-------------|
| [Flutter Developer Guide](flutter-dev/index.md) | Architecture, state management, and contribution guidelines |
| [Flutter API](flutter-api/index.html) | Auto-generated Dart API documentation |

## Quick Links

- **Source Code**: [github.com/mattaq31/Hash-CAD](https://github.com/mattaq31/Hash-CAD)
- **PyPI Package**: [crisscross-kit](https://pypi.org/project/crisscross-kit/)
- **Issues & Feedback**: [GitHub Issues](https://github.com/mattaq31/Hash-CAD/issues)
- **#-CAD Web**: [hash-cad.com](https://www.hash-cad.com)

---

## Quick Installation Reference

=== "Desktop App"

    Download the latest release from [GitHub Releases](https://github.com/mattaq31/Hash-CAD/releases).

=== "Python Library"

    ```bash
    pip install crisscross_kit
    ```
---

!!! quote "Citation"
    If you use #-CAD or the various Python libraries in your research, please cite our work (details coming soon).
