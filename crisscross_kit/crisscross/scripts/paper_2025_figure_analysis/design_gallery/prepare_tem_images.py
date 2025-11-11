import os
import re
import tifffile
import numpy as np
from skimage.transform import rescale
from skimage.util import img_as_float32
from imageio import imwrite
import cv2

def parse_tiff_calibration(image_file):

    with tifffile.TiffFile(image_file) as tif:
        # Get the description metadata (usually stored in ImageDescription tag)
        desc = tif.pages[0].tags.get('ImageDescription')
        if desc is None:
            raise ValueError("No 'ImageDescription' metadata found in TIFF.")

    desc = desc.value

    # Normalize line endings and remove unwanted spaces and terms
    desc = desc.replace('\r', '\n')
    desc = desc.replace('ResolutionUnit', '')
    desc = desc.replace(' ', '')

    # Helper function to extract values using regex
    def extract_value(key):
        match = re.search(rf"{key}=([^\n]+)", desc)
        if not match:
            raise ValueError(f"Key '{key}' not found in metadata.")
        return match.group(1).strip()

    # Extract metadata values
    xpixcal = float(extract_value("XpixCal"))
    ypixcal = float(extract_value("YpixCal"))
    unit = extract_value("Unit")

    # Compute scale (inverted)
    unit_per_pixel = 1.0 / xpixcal

    # Print results
    print(f"TEM scale is {unit_per_pixel} {unit}/pixel")

    # Return results if needed
    return {
        "XpixCal": xpixcal,
        "YpixCal": ypixcal,
        "Unit": unit,
        "UnitPerPixel": unit_per_pixel
    }


root_dir = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Papers/hash_cad/design_library'

pixel_size_standard = 1.011 # nm/pix
crop_size = (1752, 1554)

designs = {
    'daffodil':{
        'zoom_im': '20250423_B8_SW129_hexstar_32handle_1stpulldown_10pM_2.tif',
        'crop_coords': (179, 53)
    },
    'fox':{
        'zoom_im': '9_days_incubation/20250826-Purified_fox_22.tif',
        'crop_coords': (1621, 694)
    },
    'glider':{
        'zoom_im': '20240702_MA007_whitegridholder_Q2_solnasmblpulldown_10xdilution_0.tif',
        'crop_coords': (220, 310)
    },
    'handaxe':{
        'zoom_im': 'Handaxe 106h/Handaxe_1_15K_5.tif',
        'crop_coords': (344, 111)
    },
    'hexagon':{
        # 'zoom_im': 'hexa_low_conc/hexa_high_conc_6.tif', # positive stain version
        'zoom_im': 'hexa_capc_reimaging_by_yichen_oct_29_2025/ass hex 6.tif',
        # 'crop_coords': (843, 237)
        'crop_coords': (296, 243)
    },
    'rigid_square':{
      'zoom_im': 'rigid Corey dilute neg stain ua 7.tif',
      'crop_coords': (300, 1)
    },
    'lily':{
        'zoom_im': 'Lily 84h/Lily88h_06.tif',
        'crop_coords': (1212, 150)
    },
    'megastar':{
        'zoom_im': 'Megastar 106h/Megastar_1_15K_4.tif',
        'crop_coords': (1600, 554)
    },
    'recycling':{
        'zoom_im': 'purified/recycling_low_con_12.tif',
        'crop_coords': (1480, 457)
    },
    'shuriken':{
        'zoom_im': 'Shuriken 44h/Shuriken_44h_002.tif',
        'crop_coords': (2216, 667)
    },
    'sunflower':{
        'zoom_im': 'Sunflower V0 for MAD-C4 106h/Sunflower_1_30K_5.tif',
        'crop_coords': (900, 1)
    },
    'turnstile':{
        'zoom_im': 'Turnstile 84h/Turnstile84_04.tif',
        'crop_coords': (800, 40)
    },
    'bird':{
        # dealt with separately
    }
}

for design, specs in designs.items():
    if len(specs) == 0:
        continue

    print('Loading TEM image for design:', design)
    design_folder = os.path.join(root_dir, design)
    tem_folder = os.path.join(design_folder, 'tem_images')
    paper_graphics_folder = os.path.join(design_folder, 'paper_graphics')

    image_file = os.path.join(tem_folder, specs['zoom_im'])
    output_file = os.path.join(paper_graphics_folder, f'{design}_gallery_tem_cropped.png')
    img = tifffile.imread(image_file)
    calibration_data = parse_tiff_calibration(image_file)
    pixel_size_im = calibration_data['UnitPerPixel']
    if calibration_data['Unit'] != 'nm':
        pixel_size_im = pixel_size_im  * 1000 # convert to nm
    scale_factor = pixel_size_im / pixel_size_standard
    print(f'Scaling image by factor: {scale_factor}')

    # Rescale image
    img_float = img_as_float32(img)

    # Rescale image
    img_rescaled = rescale(
        img.astype(np.float32),
        scale= scale_factor,  # invert: larger pixel size → smaller image
        anti_aliasing=True,
        channel_axis=None,
        preserve_range=True  # keep original intensity range
    ).astype(img.dtype)

    # save one example of a full image
    if design == 'hexagon':
        imwrite(os.path.join(paper_graphics_folder, f'{design}_gallery_full_image.png'), img_rescaled)

    # Crop to defined region (if applicable)
    if 'crop_coords' in specs:
        x0, y0 = specs['crop_coords']
        y0 = int(y0 * scale_factor)
        x0 = int(x0 * scale_factor)
        y1, x1 = y0 + crop_size[0], x0 + crop_size[1]
        img_rescaled = img_rescaled[y0:y1, x0:x1]

    # Save as 16-bit PNG
    imwrite(output_file, img_rescaled)

    print("------")

# running the colored hexagon image separately due to additional complications
input_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Papers/hash_cad/design_library/Colored hexagon/fluoro_export_images/imag1'
output_folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Papers/hash_cad/design_library/Colored hexagon/paper_graphics'

# file setup
colored_hexa_image_input = os.path.join(input_folder, 'Composite-2.tif')
colored_hexa_output_file = os.path.join(output_folder, 'colored_hexa_crop_scaled.tif')
colored_hexa_output_c1 = os.path.join(output_folder, 'colored_hexa_crop_scaled_c1.png')
colored_hexa_output_c2 = os.path.join(output_folder, 'colored_hexa_crop_scaled_c2.png')
colored_hexa_output_viewing = os.path.join(output_folder, 'colored_hexa_crop_for_viewing.tif')

# specs and scale factor
colored_hexa_pixel_size = 43.261763955 # nm/pix
img = tifffile.imread(colored_hexa_image_input)
scale_factor = colored_hexa_pixel_size / pixel_size_standard
print(f'Scaling colored hexagon image by factor: {scale_factor}')

# Ensure channels-last (Y, X, C)
if img.ndim == 3 and img.shape[-1] not in (2, 3, 4) and img.shape[0] in (2, 3, 4):
    img = np.moveaxis(img, 0, -1)

# Rescale image using opencv (to speed things up)
img_rescaled = cv2.resize(
    img,
    None,
    fx=scale_factor,
    fy=scale_factor,
    interpolation=cv2.INTER_NEAREST
)

# crop out image here.  Extended crop size to fit in the full hexagon properly.
x0 = 45
y0 = 40
y0 = int(y0 * scale_factor)
x0 = int(x0 * scale_factor)
y1, x1 = y0 + crop_size[0] + 500, x0 + crop_size[1] + 500
img_rescaled = img_rescaled[y0:y1, x0:x1, :]

# need to rescale each channel since they are using a very tiny part of the 16-bit range

# Channel 1
c1 = img_rescaled[..., 0].astype(np.float32)
c1_min, c1_max = c1.min(), c1.max()
img_c1_scaled = ((c1 - c1_min) / (c1_max - c1_min) * 65535).astype(np.uint16)

# Channel 2
c2 = img_rescaled[..., 1].astype(np.float32)
c2_min, c2_max = c2.min(), c2.max()
img_c2_scaled = ((c2 - c2_min) / (c2_max - c2_min) * 65535).astype(np.uint16)

# blue channel will be full of 0s
composite_rgb_image = np.zeros((img_rescaled.shape[0], img_rescaled.shape[1], 3), dtype=np.uint16)

composite_rgb_image[...,0] = img_c1_scaled  # Red channel
composite_rgb_image[...,1] = img_c2_scaled  # Green channel

# saving the full image combined and separately just in case
tifffile.imwrite(colored_hexa_output_file, img_rescaled, planarconfig='contig', metadata={'axes': 'YXS'})
imwrite(colored_hexa_output_c1, img_c1_scaled)
imwrite(colored_hexa_output_c2, img_c2_scaled)

# saving a pre-blended version for direct placement inside a figure
tifffile.imwrite(colored_hexa_output_viewing, composite_rgb_image)





