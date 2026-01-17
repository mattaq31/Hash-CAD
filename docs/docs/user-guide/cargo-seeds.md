# Cargo and Seeds
## Cargo

One of crisscross origami's unique selling points is its ability to attach cargo anywhere on its lattice by replacing assembly handles with cargo tag handles.

'Cargo' refers to payload molecules that are attached to specific positions on slats, typically for carrying functional groups, markers, or therapeutic molecules.  For #-CAD, cargo specifically refers to a unique DNA sequence placed instead of an assembly handle, which can be used to subsequently bind to a target cargo molecule by hybridization.

### Adding Cargo

1. Select the **Cargo & Seed** sidebar 
2. Click on **Add** under the cargo palette
3. Name your cargo and assign it a short name and color
4. Select your newly created cargo type from the palette
5. Place cargo tags anywhere on the 2D design canvas, in the same way you would place an assembly handle
6. You can place cargo in batches (similar to slats) by editing the cargo addition count.  You can also place cargo on either the top or bottom side of a slat by changing the selector on the sidebar.

!!! tip "Cargo Naming"
    After your design is complete, you will need your robotic liquid handler to assign special DNA sequences to match your cargo tags.  Make sure to set the same name as that used in your DNA plate, otherwise the system will not be able to match the cargo tag with its correct sequence.

!!! tip "Cargo toggle"
    Cargo handles can be manually toggled on/off from the 2D or 3D grid visualization setting menus (bottom left of each panel)

<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/tutorial_kit/cargo_add.gif" alt="Cargo addition" width="800">
</p>

### Editing Cargo

Cargo can be edited in the same way as assembly handles - simply click on a cargo tag in edit mode to move it around or delete it entirely.

The cargo color can be adjusted after creation from the cargo palette.

!!! tip "Cargo Priority"
    Cargo tags always take priority over assembly handles, and can thus be used to overwrite over assembly handles entirely.

<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/tutorial_kit/cargo_edit.gif" alt="Cargo editing" width="800">
</p>

## Seeds

Seeds are specialized DNA origami structures that are used to initiate megastructure assembly.  They have 80 sockets (spread over a 5x16 grid) to which slats can bind, and are used to initiate assembly of the whole megastructure.  

### Placing Seeds

1. Select the **Cargo & Seed** sidebar
2. Select the seed pictogram from the cargo palette
3. Place in your design as you would a normal cargo tag
4. Seeds have additional design rules - they cannot overlap a slat on an opposing layer, they need to bind to at least 16 unique slats (or slat barrels) and have special naming conventions that cannot be renamed
5. Multiple seeds can be placed in a design, although this is rare to do in practice

!!! tip "Seed color"
    Seed color can be adjusted in the same way as a cargo tag.

<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/tutorial_kit/seed_add.gif" alt="Seed addition example" width="800">
</p>
