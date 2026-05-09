# Echo Export

\#-CAD can export your megastructure design directly to command sheets for the [Echo Liquid Handler](https://www.beckman.com/liquid-handlers/echo-acoustic-technology), enabling automated assembly of your DNA origami monomer slats (refer to our accompanying paper for more details on laboratory assembly).

## Overview

The Echo export workflow:

1. Configure source plates (where DNA handles are stored)
2. Link design handles with sequences from source plates
3. Assign slats to output 96-well plates via the Echo Plate Layout window
4. Configure per-well dispensing parameters (ratio, volume, scaffold concentration)
5. Optionally mark specific handles as manual (pipetted by hand)
6. Generate export outputs (CSV commands, PDF reports, master mix sheets, PEG purification sheets)

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

<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/tutorial_kit/echo_export.gif" alt="Echo export example" width="800">
</p>

## Echo Plate Layout

The Echo Plate Layout window provides a drag-and-drop interface for assigning slats to 96-well output plates:

- **Auto-assign**: Places slats in sorted order, optionally split by slat type or layer
- **Duplicate slats**: Create multiple copies of a slat across plates
- **Per-well config**: Set ratio, volume, and scaffold concentration per well or in bulk
- **Manual handles**: Mark specific handle positions that should be pipetted by hand rather than dispensed by the Echo
- **Volume normalization**: Optionally equalize total volume across wells with water compensation

Plate assignments are persisted within the design file in a consolidated `output_echo_plates` sheet.

## Export Outputs

The export system generates multiple output files:

| Output | Description |
|--------|-------------|
| **Echo CSV** | Transfer instructions for the Echo liquid handler (source plate, source well, destination well, volume) |
| **Manual CSV** | Separate instruction list for handles marked as manual |
| **PDF Report** | Visual plate layout with handle barcodes, well configs, and colour coding |
| **Master Mix Sheet** | Excel workbook with per-slat-type volume calculations for master mix preparation |
| **PEG Purification Sheet** | Excel workbook with per-group PEG purification calculations |

## Design File Format

When echo plates are configured, the design `.xlsx` file includes:

- `output_echo_plates` sheet — consolidated plate assignments and well configs for all plates
- `input_source_plates` sheet — all loaded input plate definitions
- `lab_metadata` sheet — export flags, master mix config, and PEG config key-value pairs
