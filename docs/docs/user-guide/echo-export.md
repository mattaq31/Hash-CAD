# Echo Export (FEATURE STILL IN BETA)

\#-CAD can export your megastructure design directly to command sheets for the [Echo Liquid Handler](https://www.beckman.com/liquid-handlers/echo-acoustic-technology), enabling automated assembly of your DNA origami monomer slats (refer to our accompanying paper for more details on laboratory assembly).

## Overview

The Echo export workflow:

1. Configure source plates (where DNA handles are stored)
2. Link design handles with sequences from source plates
3. Set export parameters (volumes, concentrations)
4. Generate command sheets
5. Run on Echo Liquid Handler

## Prerequisites

Before considering an Echo export, ensure:

- [ ] Your design has optimized assembly handles
- [ ] All cargo and seed elements are placed
- [ ] Source plates are configured with available handles (the plates used by the crisscross origami team are available [here](https://github.com/mattaq31/Hash-CAD/tree/main/crisscross_kit/crisscross/dna_source_plates), we are working on a tutorial for setting up your own plates)

## Import plates into #-CAD

1. Switch to the **Echo Config** sidebar tab
2. Load your handle plates from file
3. Turn on the **Plate Validation** visualization from the 2D grid settings
4. Click on the **Assign** button to assign handles to each plate well
5. Adjust the total output quantity of each handle (currently split as **reference volume** and **reference concentration**)
6. Export the commands

<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/tutorial_kit/echo_export.gif" alt="Echo export example" width="800">
</p>

Further Details TBC!
