import os
import numpy as np
import matplotlib.pyplot as plt
import math
import matplotlib.patches as patches
import matplotlib.transforms as mtransforms

PlusGrowth = ["nucX asymmetrical", "up", "right", "down", "right", "down", "left", "down", "left", "up","left"]
BoxGrowth = ["nucX mirrored", "down", "right", "down", "right","down","left","down","left","down"]
SGrowth = ["nucX 180", "down", "right", "down", "left", "down", "left", "up", "left"]
BatGrowth = ["nucX flipped", "down", "right", "down", "right", "down"]

SlatInfoDict = {}
SlatInfoDict["nucX asymmetrical"] = {"type":"nucX asymmetrical", "color":"#6D6D6D", "direction":1} 
SlatInfoDict["nucX mirrored"] = {"type":"nucX mirrored", "color":"#6D6D6D", "direction":1} 
SlatInfoDict["nucX 180"] = {"type":"nucX 180", "color":"#6D6D6D", "direction":1} 
SlatInfoDict["nucX flipped"] = {"type":"nucX flipped", "color":"#6D6D6D", "direction":1} 
SlatInfoDict["right"] = {"type":"X", "color":"#F9708E", "direction":1}
SlatInfoDict["left"] = {"type":"X", "color":"#FFB531", "direction":-1}
SlatInfoDict["down"] = {"type":"Y", "color":"#60EF54", "direction":-1}
SlatInfoDict["up"] = {"type":"Y", "color":"#5CB6FF", "direction":1}

def growth_front_debug_helper(growth_fronts, global_ax, all_markers=None):
    # all_markers is a tuple of lists: (topleftmarker, toprightmarker, bottomrightmarker, bottomleftmarker)
    # Could technically make this a single list, but this is more readable

    if all_markers is None:
        topleftmarker = []
        toprightmarker = []
        bottomrightmarker = []
        bottomleftmarker = []

    else:
        topleftmarker, toprightmarker, bottomrightmarker, bottomleftmarker = all_markers
        for marker in topleftmarker + toprightmarker + bottomrightmarker + bottomleftmarker:
            marker[0].remove()
        topleftmarker.clear()
        toprightmarker.clear()
        bottomrightmarker.clear()
        bottomleftmarker.clear()

    for front in growth_fronts:
        top_left, top_right, bottom_right, bottom_left = front 
        # top-left is red, top-right is blue, bottom-right is black, bottom-left is green
        topleftmarker.append(global_ax.plot(top_left[0], top_left[1], 'ro', markersize=10, alpha=0.5))
        toprightmarker.append(global_ax.plot(top_right[0], top_right[1], 'bo', markersize=10, alpha=0.5))
        bottomrightmarker.append(global_ax.plot(bottom_right[0], bottom_right[1], 'ko', markersize=10, alpha=0.5))
        bottomleftmarker.append(global_ax.plot(bottom_left[0], bottom_left[1], 'go', markersize=10, alpha=0.5))

    return topleftmarker, toprightmarker, bottomrightmarker, bottomleftmarker

def repeated_units_90_degrees_combined_plot(full_growth_list, n_steps="all", save_figure=False, slats_per_block=16, \
                                            line_width=None, debug=False):
    # n_steps = "all" or a single integer to get one step of the growth process
    # n_steps = list of steps to get a single figure with all specified steps
    # If a filename is passed to save_figure, then save the image 

    if type(n_steps) == list or type(n_steps) == np.ndarray:
        n_steps_total = max(n_steps) # sets linewidth to the rec'd value for the largest step
        growth_instructions_list = [full_growth_list[:i] for i in n_steps]
        first_step = min(n_steps)
    elif type(n_steps) == int:
        n_steps_total = n_steps
        growth_instructions_list = [full_growth_list[:n_steps]] ### Changed! Update script version
        first_step = n_steps
    elif type(n_steps) == str and n_steps == "all":
        n_steps_total = len(full_growth_list)
        growth_instructions_list = [full_growth_list]
        first_step = 1

    plt.close()
    global_fig, global_ax = plt.subplots(1, len(growth_instructions_list), figsize=(len(growth_instructions_list) * 10, 10)) 
    
    if len(growth_instructions_list) == 1:
        global_ax = [global_ax] # Ensure global_ax is always a list for consistency

    for n, growth_instructions in enumerate(growth_instructions_list):
        # Keep track of "live" areas or growth fronts that we can have slats attach to 
        # top-left, top-right, bottom-right, bottom-left
        growth_fronts = [((0,slats_per_block/4), (slats_per_block/2, slats_per_block/4), \
                        (slats_per_block/2, -slats_per_block/4), (0, -slats_per_block/4))] 
        
        # DEBUG: Plot the growth fronts
        if debug:
            debug_markers = growth_front_debug_helper(growth_fronts, global_ax[n])

        if line_width is None:
            C0 = 10.0
            #slat_width = C0/(int(math.sqrt(len(growth_instructions)))*slats_per_block)
            slat_width = C0/(int(n_steps_total**(1/2))) # scales better with 1/n^0.75 than 1/sqrt(n) instructions
        else:
            slat_width = line_width

        for nth_step, growth_step in enumerate(growth_instructions):
            # Process slat information and set slat block geometry depending on values
            slat_orientation = SlatInfoDict[growth_step]["type"]
            slat_direction = SlatInfoDict[growth_step]["direction"]
            new_growth_fronts = []
            for front in growth_fronts:
                top_left, top_right, bottom_right, bottom_left = front 
                
                if slat_orientation in ("X", "nucX asymmetrical", "nucX mirrored", "nucX 180", "nucX flipped"):
                    slat_laying_direction = np.sign(top_left[1]-bottom_right[1]) # orthogonal to slats
                    slat_drawing_direction = np.sign(top_right[0]-top_left[0]) # parallel to slats
                    # The factor of 0.25 is to ensure that the slats are not too close to the edges on their LONG side
                    y_positions = np.linspace(top_left[1]-slat_laying_direction*0.25, bottom_right[1]+slat_laying_direction*0.25, slats_per_block)
                    x_start = (bottom_right[0]+top_left[0])/2 + slat_direction*(top_left[0]-bottom_right[0])/2
                    for i in range(slats_per_block):
                        start_pos = (x_start, y_positions[i])
                        end_pos = (x_start + slat_drawing_direction*slat_direction*slats_per_block, y_positions[i])
                        # The factor of 0.18 is to ensure that slats are drawn a little shorter, so that there's a gap between two abutting slats
                        global_ax[n].plot([start_pos[0] + slat_drawing_direction*slat_direction*0.18, \
                                        end_pos[0] - slat_drawing_direction*slat_direction*0.18], 
                                    [start_pos[1], end_pos[1]], color=SlatInfoDict[growth_step]["color"], \
                                linewidth=slat_width, alpha=0.7, zorder=1)
                        
                    # update new growth front - shift it over. Only do this once per growth step
                    new_top_left = (top_left[0] + slat_drawing_direction * slat_direction * slats_per_block/2, top_left[1])
                    new_top_right = (top_right[0] + slat_drawing_direction * slat_direction * slats_per_block/2, top_right[1])
                    new_bottom_right = (bottom_right[0] + slat_drawing_direction * slat_direction * slats_per_block/2, bottom_right[1])
                    new_bottom_left = (bottom_left[0] + slat_drawing_direction * slat_direction * slats_per_block/2, bottom_left[1])
                    new_growth_fronts.append((new_top_left, new_top_right, new_bottom_right, new_bottom_left))

                    # Separate if block for splitting into two growth fronts; some corners are shared
                    if slat_orientation == "nucX mirrored":
                        new_growth_fronts.append((new_top_left, top_left, bottom_left, new_bottom_left))

                    elif slat_orientation == "nucX 180":
                        new_growth_fronts.append((bottom_right, bottom_left, top_left, top_right))
                        
                    elif slat_orientation == "nucX flipped":
                        new_growth_fronts.append((bottom_left, bottom_right, top_right, top_left))
                        
                elif slat_orientation == "Y": 
                    slat_laying_direction = np.sign(bottom_right[0]-top_left[0]) # orthogonal to slats
                    slat_drawing_direction = np.sign(top_left[1]-bottom_left[1]) # parallel to slats
                    x_positions = np.linspace(top_left[0]+0.25*slat_laying_direction, bottom_right[0]-slat_laying_direction*0.25, slats_per_block)
                    y_start = (bottom_right[1]+top_left[1])/2 + slat_direction*(bottom_right[1]-top_left[1])/2
                    for i in range(slats_per_block):
                        start_pos = (x_positions[i], y_start)
                        end_pos = (x_positions[i], y_start + slat_drawing_direction * slat_direction * slats_per_block)
                        global_ax[n].plot([start_pos[0], end_pos[0]],\
                                    [start_pos[1] + slat_drawing_direction * slat_direction*0.18, \
                                        end_pos[1] - slat_drawing_direction * slat_direction*0.18], \
                                    color=SlatInfoDict[growth_step]["color"], \
                                linewidth=slat_width, alpha=0.7, zorder=2)
                        
                    # update new growth front
                    new_top_left = (top_left[0], top_left[1] + slat_drawing_direction * slat_direction * slats_per_block/2)
                    new_top_right = (top_right[0], top_right[1] + slat_drawing_direction * slat_direction * slats_per_block/2)
                    new_bottom_right = (bottom_right[0], bottom_right[1] + slat_drawing_direction * slat_direction * slats_per_block/2)
                    new_bottom_left = (bottom_left[0], bottom_left[1] + slat_drawing_direction * slat_direction * slats_per_block/2)
                    new_growth_fronts.append((new_top_left, new_top_right, new_bottom_right, new_bottom_left))
        
                # A separate if system, to add a seed (for aesthetics) to the bottom-most layer if it was a nucX
                if "nucX" in slat_orientation: # Assumes a "right" nucX slat
                    gridiron = patches.Rectangle(
                        (bottom_right[0]-1.25*slats_per_block / 16 - 0.25*slats_per_block / 16, bottom_right[1]), # lower-left corner
                        1.25*slats_per_block / 8, # rectangle width
                        slats_per_block/2, # rectangle height
                        facecolor="#DE3C32",
                        edgecolor="none",
                        alpha=0.7,
                        zorder=0
                    )
                    global_ax[n].add_patch(gridiron)
        
            # Update the growth front
            growth_fronts = new_growth_fronts

            # DEBUG: Plot the new growth fronts; first remove old markers
            if debug:
                growth_front_debug_helper(growth_fronts, global_ax[n], debug_markers)
        
        # Plot aesthetics
        radius_of_plot = int(math.sqrt(len(growth_instructions)))*slats_per_block
        global_ax[n].set_xlim(-radius_of_plot-4, radius_of_plot+4)
        global_ax[n].set_ylim(-radius_of_plot-4, radius_of_plot+4)
        global_ax[n].axis('scaled')
        global_ax[n].axis('off')
        if type(n_steps) != str:
            global_ax[n].set_title("Step {}".format(nth_step+first_step), fontsize=48, pad=20)
    
    # Get limits from the last subplot
    xlim = global_ax[-1].get_xlim()
    ylim = global_ax[-1].get_ylim()

    # Apply these limits to all subplots
    for ax in global_ax:
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_aspect('equal')  # or ax.axis('scaled')

    # Save fig to file
    if save_figure:
        global_fig.savefig(save_figure, bbox_inches='tight', dpi=300)

    return