# Designing Slats

The 2D grid view is the primary workspace for designing megastructure layouts. This guide covers the basics of working with slats, and some essential design rules. 

## Grid Basics

All controls used in this section are located within the `Slat Design` sidebar.

### Grid Modes

\#-CAD supports two grid geometry modes:

| Mode               | Description | Grid Angle |
|--------------------|-------------|------------|
| **Square Grid**    | Orthogonal slat intersections | 90°        |
| **Hexagonal Grid** | Hexagonal slat arrangements | 60°        |
In a square grid, slats can be placed either vertically or horizontally. 
<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/tutorial_kit/90deg_grid.png" alt="90deg" width="300">
</p>
In a hexagonal grid, slats can be placed in three directions at 60° intervals. 
<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/tutorial_kit/60deg_grid.png" alt="60deg" width="500">
</p>

'Triangulation' is achieved when slats in all three directions spanning multiple layers are bound to each other.  Triangulation prevents slats from shearing with respect to each other, and results in a more rigid design.
<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/tutorial_kit/triangulated.png" alt="Triangulation" width="600">
</p>

Toggle between modes using the grid mode selectors in the slat design sidebar.

### Navigation

| Action              | Control                                                                                                                      |
|---------------------|------------------------------------------------------------------------------------------------------------------------------|
| **Pan**             | Click and drag on empty space, or middle-mouse drag                                                                          |
| **Zoom**            | Scroll wheel, or pinch gesture on trackpad (will zoom on cursor)                                                             |
| **Center on slats** | To center the view on the slats in your design, click on the centering button at the bottom left of the canvas (shown below) |

## Working with Slats

### Adding Slats

1. Select **Add** from the mode selector.
2. Hover over the grid to show a preview of the slat placement, which will automatically snap to your selected grid.
3. Click to place your slat.
4. You can change slat type from the slat palette, or change the number of slats you want to add in one go by changing the slat addition count.
5. Slats can be rotated by pressing the 'R' key and, when placing multiple slats, flipped by pressing the 'F' key (try them out to get a feel for how these commands work).
6.  Slats can only be placed on one layer at a time.  Switch between layers by clicking on the different layers in the layer manager, or cycle through them using the up/down arrow keys.  You can also quickly add a new layer by pressing the 'A' key.
7. **ctrl-z** or **cmd-z** allows you to undo the last slat placement.

**NOTE - GIF IS USING AN OLDER VERSION THAT ALSO INCLUDED THE T KEY FOR FLIPPING SLATS - IGNORE THIS, GIF WILL BE UPDATED SOON**
<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/tutorial_kit/slat_add.gif" alt="Triangulation" width="800">
</p>

!!! tip "3D Viewer"
    The 3D viewer can be used to monitor your design while it's being built.  You can also show a visual hover of a slat as you move around the 2D grid.  The 3D viewer also has the option to display slats as honeycomb tubes (similar to their real 6hb implementation), but this may slow down rendering for large designs.

### Editing Slats

1. Switch to the **Edit** mode.
2. Select slats by clicking on them.  A shift-click allows you to select multiple slats.  By holding down ctrl or cmd, you can also select multiple slats at once.
3. After selecting a slat, you can either drag them to a different position, delete them by pressing the 'Delete' or 'Backspace' keys, or transposed by pressing the 'T' key.
4. You may also select the **Delete** mode to delete slats directly with a single click.

!!! tip "Color"
    While the layer dictates the default color for a slat, you may change the color of individual slats from the 'edit' tab.

<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/tutorial_kit/slat_edit.gif" alt="Triangulation" width="800">
</p>

## Layers

Complex megastructures use multiple layers of slats that stack vertically.

### Layer Management

- **Add Layer**: Use the layer panel or press the `A` key.
- **Delete Layer**: Click on the red X button on the target layer.
- **Move Layer**: Drag and drop layers to your target position from the layer manager.
- **Hide/Show Layer**: Click the eye icon on the target layer.
- **Flip Layer**: Click the flip icon on the target layer to invert slat orientations.
- **Change layer colour**: Click on the target layer's color swatch to edit the color of all slats on that layer.

You may also isolate only the currently selected layer from the toggle switch in the layer manager.

<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/tutorial_kit/layers.gif" alt="Triangulation" width="800">
</p>

!!! tip "Visualization"
    There are a number of visualization settings you may edit for both the 3D and 2D views from their respective visual settings.  For example, you can shorten slats slightly to visualize seams, show individual slat IDs, or preview the slat direction for the 2D grid.

## Undo/Redo

\#-CAD maintains a full undo history:

- **Undo**: `Cmd/Ctrl + Z`
- **Redo**: `Cmd/Ctrl + Shift + Z` or `Cmd/Ctrl + Y`

## Saving Your Design

Designs are saved in Excel format (`.xlsx`), compatible with both #-CAD and the Python `crisscross` library.

- **Save**: Click on the export button in the top left of the sidebar.
- **Load**: Click on the import button in the top left of the sidebar, or drag and drop a file onto the 2D grid.

You can edit your design's name from the top floating window containing the design title.

!!! tip "Export to SVG"
    You can also export your 2D design as an SVG file from the camera button on the top left of the grid, allowing you to directly edit the design in Illustrator, Affinity or Inkscape (or otherwise).

