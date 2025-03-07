import os
from colorama import Fore
from crisscross.helper_functions.plate_constants import plate96, plate384
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Patch
from string import ascii_uppercase
from collections import Counter
import platform

# consistent figure formatting between mac, windows and linux
if platform.system() == 'Darwin':
    plt.rcParams.update({'font.sans-serif': 'Helvetica'})
elif platform.system() == 'Windows':
    plt.rcParams.update({'font.sans-serif': 'Arial'})
else:
    plt.rcParams.update({'font.sans-serif': 'DejaVu Sans'}) # should work with linux



def visualize_plate_with_color_labels(plate_size, well_color_dict,
                                      color_label_dict=None,
                                      well_label_dict=None,
                                      plate_title=None, save_folder=None,
                                      save_file=None, direct_show=True,
                                      plate_display_aspect_ratio=1.495):
    """
    Use this function to create a plate graphic with specific colours placed in each well, and alternatively a unique
    label for each well too.
    :param plate_size: '384' or '96'
    :param well_color_dict: Dictionary containing colour to be placed in specific wells.
    :param color_label_dict: Legend to use for specific colours (at the bottom of the image)
    :param well_label_dict: Optional label to place in specific wells
    :param plate_title: Title to display above plate
    :param save_folder: Output folder
    :param save_file: Output file name
    :param direct_show: Set to true to display the image directly
    :param plate_display_aspect_ratio: Aspect ratio to use for plate display
    :return: N/A
    """

    # prepares the graphical elements of the two plate types
    if plate_size == '96':
        row_divider = 12
        total_row_letters = 8
        plate = plate96
    elif plate_size == '384':
        row_divider = 24
        total_row_letters = 16
        plate = plate384
    else:
        raise RuntimeError('Plate size can only be 96 or 384.')


    fig, ax = plt.subplots(figsize=(total_row_letters * plate_display_aspect_ratio, total_row_letters))

    # Draws the rectangular box for the plate border
    rect = Rectangle((0, 0),
                     total_row_letters * plate_display_aspect_ratio,
                     total_row_letters,
                     linewidth=0.5, edgecolor='black', facecolor='none')
    ax.add_patch(rect)

    for well_index, well in enumerate(plate):
        x = well_index % row_divider + 0.5  # the 0.5 is there to make things easier to view
        y = well_index // row_divider + 0.5

        if well in well_color_dict:
            color = well_color_dict[well]
            circle = Circle((x, y), radius=0.3, fill=True, facecolor=color, edgecolor='black')
            # adds the well label if it exists
        else:
            # empty well
            circle = Circle((x, y), radius=0.3, fill=None)

        if well_label_dict is not None and well in well_label_dict:
            ax.text(x, y, well_label_dict[well] if isinstance(well_label_dict[well], str) else str(well_label_dict[well]), ha='center', va='center', fontsize=12)

        ax.add_patch(circle)

    # adding lines to help with well identification
    plt.hlines(y=total_row_letters/2, color='black', linewidth=1, linestyle='dashed',
                xmin=0, xmax=total_row_letters * plate_display_aspect_ratio)
    plt.hlines(y=total_row_letters/4, color='black', linewidth=1, linestyle='dashed',
                xmin=0, xmax=total_row_letters * plate_display_aspect_ratio)
    plt.hlines(y=(3*total_row_letters)/4, color='black', linewidth=1, linestyle='dashed',
                xmin=0, xmax=total_row_letters * plate_display_aspect_ratio)

    plt.vlines(x=row_divider/2, color='black', linewidth=1, linestyle='dashed',
                ymin=0, ymax=total_row_letters)
    plt.vlines(x=row_divider/4, color='black', linewidth=1, linestyle='dashed',
                ymin=0, ymax=total_row_letters)
    plt.vlines(x=(3*row_divider)/4, color='black', linewidth=1, linestyle='dashed',
                ymin=0, ymax=total_row_letters)

    # Set the y-axis labels to the plate letters
    ax.set_yticks([i + 0.5 for i in range(total_row_letters)])
    ax.set_yticklabels(ascii_uppercase[:total_row_letters], fontsize=18)
    ax.yaxis.set_tick_params(pad=15)
    ax.tick_params(axis='y', which='both', length=0)

    # Set the x-axis labels to the plate numbers
    ax.set_xticks([i + 0.5 for i in range(row_divider)])
    ax.set_xticklabels([i + 1 for i in range(row_divider)], fontsize=18)
    ax.tick_params(axis='x', which='both', length=0)
    ax.xaxis.tick_top()

    # deletes the axis spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    # sets limits according to number of rows/cols.  Y-axis is inverted to make it easier for compatibility with different plate types
    ax.set_xlim(0, row_divider)
    ax.set_ylim(total_row_letters, -0.1)

    if plate_title:
        plt.suptitle(plate_title, y=0.99, fontsize=35)

    if color_label_dict:
        # legend creation
        labels = list(color_label_dict.values())
        colors = list(color_label_dict.keys())
        wedges = [Patch(facecolor=color, edgecolor='black', label=label) for color, label in zip(colors, labels)]

        ax.legend(wedges, labels,
                  loc='upper center',
                  bbox_to_anchor=(0.5, 0.0), ncol=5,
                  fancybox=True, fontsize=18)


    plt.tight_layout()
    if save_file and save_folder:
        plt.savefig(os.path.join(save_folder, f'{save_file}.pdf'))
    if direct_show:
        plt.show()
    plt.close()
