# Assembly Handles
Once slats are placed on the canvas, the next step is to assign assembly handles.

Assembly handles bind slats together to build up a megastructure (using the crisscross principle).  

## Assembly Handle Basics

Each slat position has two handle sites; 'H (helix) 2' and 'H5'. 'Helix' refers to the specific DNA origami helix from which the assembly handle staples would extend out of.

When slats intersect, a handle (+) extending from one slat joins with the opposite complementary handle (-) on the other slat and hybridize into a crisscross bond.  A single such bond is not enough to stabilize a slat-slat connection, but several of these bonds at different positions along the slat length create a much stronger connection (see our paper for more info).

Assembly handles are displayed directly on the 2D canvas (and on the 3D viewer if the option is turned on).  These are represented as colored boxes with their integer ID displayed.  These can be toggled on/off from the visualization settings.

<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/tutorial_kit/handle_view.png" alt="Handle view labels" width="800">
</p>

<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/tutorial_kit/view_handles.gif" alt="Handle view example" width="800">
</p>

## Handle Optimization

Most crisscross designers only have a limited number of handle sequences available to them (e.g. the Shih Lab uses a total of 64 orthogonal 7-mer sequences).  If these handles were to be assigned to a design's crisscross points randomly, many undesired (`parasitic') interactions will become possible between slats outside of the intended final assembly.


<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/tutorial_kit/randomize.gif" alt="Randomized handles" width="800">
</p>

Our evolutionary algorithm attempts to find optimal handle assignments that minimize these parasitic interactions (our paper goes into much more detail on this process).

### Evolving Handles

1. Switch to the **Assembly Handles** sidebar
2. Adjust your library size (defaults to 64) from the sidebar
3. Click on the **Evolve** button 
4. Click **Start**
5. Monitor progress via the valency charts. Valency refers to how many bonds are possible between two slats e.g. a valency of 2 indicates that two slats could bind to each other using two assembly handles (at any point along their length). Your goal is to minimize the valency as much as possible.  The max valency refers to the worst case interaction between any two slats in your design.  The effective valency refers to the probabilistic average possible bonds between any two slats in your design.
6.  The best possible scenario is a max valency of 1, but designs should still assemble well with valencies ranging from 2 to 5 (the lower the better).

<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/tutorial_kit/evo_window.png" alt="Evo window" width="500">
</p>


7.  For simple designs, evolution should just take a few minutes to complete (you may continue using #-CAD while the algorithm is running).  For larger designs, the process may take hours (or even days!).

<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/tutorial_kit/evolve.gif" alt="Evo example" width="800">
</p>

### Evolution Parameters

Users may attempt to adjust evolution parameters to further optimize their results.  The below is a brief summary of their effect, although advanced customization is best carried out using our Python API:

| Parameter                  | Description                                                                              | Default                  |
|----------------------------|------------------------------------------------------------------------------------------|--------------------------|
| **Max Generations**        | Maximum generations to run                                                               | 2000                     |
| **Mutation Rate**          | Average mutations to generate per new offspring                                          | 1                        |
| **Evolution Population**   | Number of candidate solutions per generation                                             | 50                       |
| **Number of Threads**      | Number of compute threads to assign to the algorithm                                     | 2/3 of available threads |
| **Generational Survivors** | Top candidates kept each generation                                                      | 3                        |
| **Mutation Probabilities** | Probability to mutate the worst + handles, worst - handles or completely randomly        | 0.425, 0.425, 0.1        |
| **Random Seed**            | Set this to a consistent number to guarantee identical results if repeating the same run | 8                        |
| **Early Stop Target**      | Stop the evolution process early if this max valency is achieved                         | 1                        |

### Stopping Early

Click **Stop & Save** at any time to accept the current best solution. The best handles will be transferred to your design.

!!! tip "Plateauing"
    While we don't have specific rules for stoppping early, evolution often leads to an improvement of 1-2 max valency steps from a standard random handle assignment.  If the graphs plateau for more than a 1000 generations, the evolution is likely to be at its end.

### Other Controls

- **Pause**: Pause the run, while keeping progress saved
- **Export Run**: Export the best assembly handles and metrics from the run to a folder of your choice
- **Export Parameters**: Export the parameters selected for this run, which can be used to seed the same run using the Python API
- Before running evolution, one may elect to only update handles at crisscross interfaces, or else update all handles current in the design.
- Additionally, one could ensure that handles are split evenly between layers, which prevents a single handle from ever being able to bind to itself (since it would have a + handle matching a - handle on opposite sides of the slat)

<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/tutorial_kit/auto_handles.png" alt="Handle auto gen window" width="800">
</p>

## Manual Tools

Handles can also be edited manually if certain designs require more control. The **Manual Editing** section of the sidebar contains various options for editing, including:

- The ability to set or enforce specific handle IDs in 'add' mode
- The ability to move or delete handles in 'edit' mode
- The ability to mass delete or edit handles through dedicated buttons or drag-select in 'edit' mode

Other features related to linking handles are available but these are still in beta - details coming soon!

<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/tutorial_kit/handle_edit.png" alt="Handle edit window" width="600">
</p>


<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/tutorial_kit/edit_handles.gif" alt="Handle drag-select" width="800">
</p>

!!! tip "Colors"
    You can change the default colors for handles in 'edit' mode from the popup window at the bottom left of the 2D
