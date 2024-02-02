import numpy as np
from itertools import product
import matplotlib.pyplot as plt


def visualize_megastructure_slats(xMask, yMask):
    # Plots top (vertical) and bottom (horizontal) slats of the megastructure, order shown by colormap gradient
    # A little obsolete bc visualize_megastructure_handles does this too, just without gradients

    plt.figure(figsize=(8, 8))
    plt.imshow(yMask, vmin=0, vmax=np.max(yMask), cmap='coolwarm')
    plt.title("Top layer/Vertical slats")
    plt.axis('off')
    plt.show()

    plt.figure(figsize=(8, 8))
    plt.imshow(xMask, vmin=0, vmax=np.max(xMask), cmap='coolwarm')
    plt.title("Bottom layer/Horizontal slats")
    plt.xticks([])
    plt.yticks([])
    plt.show()


if __name__ == '__main__':
    rows96 = ["A", "B", "C", "D", "E", "F", "G", "H"]
    columns96 = list(np.arange(1, 12 + 1))
    plate96 = [x + str(y) for x, y in product(rows96, columns96)]

    rows384 = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"]
    columns384 = list(np.arange(1, 24 + 1))  # for leading zeros: [str(x).zfill(2) for x in np.arange(1,24+1)]
    plate384 = [x + str(y) for x, y in product(rows384, columns384)]

    DataFolder = "/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/crisscross_training/stella_scripts_and_data/20220927_megaplussign_2handlestagger/20220927_megacc6hb_plussign_2handlestagger_nonperiodic/"
    SheetNames = ["slats_top.csv", "slats_bottom.csv", "growth_top.csv", "growth_bottom.csv", "seedcontact_h2.csv"]
    Structure = "Large_Plus_Sign"

    # Import top and bottom slats
    YMask = np.loadtxt(DataFolder + SheetNames[0], delimiter=",", dtype=int)
    XMask = np.loadtxt(DataFolder + SheetNames[1], delimiter=",", dtype=int)

    visualize_megastructure_slats(XMask, YMask)

# SUB-TASKS
# 1. Design megastructure shape - 2 options, either simply draw a shape and let system guess slat positions or draw out each slat individually... (perhaps a better option would be to place slats like a jigsaw maybe?)
# 2. visualisate slats - either use heatmap system or plot out all rectanges (option 2 definitely better)
# 3. go through slat optimisation process - either follow full rotation (stella) or original method - is there a way to make this significantly faster?  Doesn't seem like something that should be slow...
# 4. Report out hamming distance and draw a graph comparing hamming distance totals (similar to Anastasia's code)
# 5. identify strands and convert into echo plate format (need to have some form of reservoir data?)

