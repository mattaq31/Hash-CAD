import os
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import create_dir_if_empty


root_dir = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Papers/hash_cad/design_library'

designs = ['Colored hexagon', 'daffodil', 'fox', 'glider', 'handaxe', 'hexagon', 'lily', 'megastar', 'recycling', 'shuriken', 'sunflower', 'turnstile']

color_library = {-1: '#2972EEFF', -2: '#C7CF00FF', -3: '#CF001AFF', -4: '#34FF17FF', -5: '#961313FF', -6: '#3B1BB1FF', -7: '#DF3AE6FF'}
color_library = {-1: '#2C007DFF', -2: '#775B00FF', -3: '#0E6D00FF', -4: '#34FF17FF', -5: '#961313FF', -6: '#3B1BB1FF', -7: '#DF3AE6FF'}
color_library = {-1: '#0057FFFF', -2: '#FF1764FF', -3: '#17B100FF', -4: '#FFF644FF', -5: '#00FFDBFF', -6: '#FFF5F4FF', -7: '#0057FFFF'}

seed_color = '#000000FF'

for design in designs:
    print('Loading design:', design)
    design_folder = os.path.join(root_dir, design)
    paper_graphics_folder = os.path.join(design_folder, 'paper_graphics')
    create_dir_if_empty(paper_graphics_folder)

    if design == 'Colored hexagon':
        design_file = os.path.join(design_folder, 'colored_hexa_with_fluoro_colors.xlsx')
    else:
        design_file = os.path.join(design_folder, f'{design}_design.xlsx')

    mega = Megastructure(import_design_file=design_file)

    parasitic_interactions = mega.get_parasitic_interactions()
    print(f'Parasitic interactions - Max valency: {parasitic_interactions["worst_match_score"]},'
          f' Eff. valency: {parasitic_interactions["mean_log_score"]}')

    if design != 'Colored hexagon':
        # editing layer colours for uniformity
        layer_count = len(mega.layer_palette)
        for key, data in mega.layer_palette.items():
            color_id = key - layer_count - 1
            if color_id in color_library:
                data['color'] = color_library.get(color_id, data['color'])

    # removing all cargo handles for cleaner visualization
    for s_id, slat in mega.slats.items():
        for pos in  range(1, 33):
            if pos in slat.H2_handles and slat.H2_handles[pos]['category'] == 'CARGO':
                slat.remove_handle(pos, 2)
            if pos in slat.H5_handles and slat.H5_handles[pos]['category'] == 'CARGO':
                slat.remove_handle(pos, 5)

    # removing all slat unique colors
    if design != 'Colored hexagon':
        for s_id, slat in mega.slats.items():
            slat.unique_color = None

    # standardize seed color
    mega.cargo_palette['SEED']['color'] = seed_color

    mega.create_blender_3D_view(paper_graphics_folder, filename_prepend=f'{design}_', animate_assembly=False, camera_spin=False)

    print('----------------')
