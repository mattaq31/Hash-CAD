from flask import current_app as app
from flask import render_template, send_file
from flask_socketio import Namespace, emit
from werkzeug.utils import secure_filename

from GUI.backend_functions.server_helper_functions import (positional_3d_array_to_dict,
                                                           positional_2d_array_and_layer_to_dict,
                                                           cargo_dict_to_formatted,
                                                           cargo_to_inventory,
                                                           convert_dict_handle_orientations_to_string,
                                                           convert_design_dictionaries_into_arrays,
                                                           combine_megastructure_arrays)
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands
from crisscross.core_functions.megastructures import Megastructure
from crisscross.helper_functions import clear_folder_contents, convert_np_to_py, zip_folder_to_disk
from crisscross.plate_mapping import get_standard_plates

import matplotlib
import os
import platform

matplotlib.use('Agg')  # Use a non-GUI backend

########## SOCKET.IO NAMESPACES AND FLASK ROUTING ##########
class SocketNamespace(Namespace):
    """
    A namespace system for the socket.io connection - this helps to route the different functions to their respective
    trigger points on the frontend.

    Each function is of format on_X, where X is the name of the function that will be called from the frontend.
    """
    def on_connect(self):
        print("A client connected to the namespace.")
        pass

    def on_disconnect(self):
        pass

    def on_get_inventory(self):
        get_inventory()

    def on_upload_file(self, data):
        upload_and_import_design(data)

    def on_generate_handles(self, data):
        generate_handles(data)

    def on_generate_megastructures(self, data):
        package_and_export_megastructure(data)

    def on_upload_plates(self, data):
        save_file_to_plate_folder(data)

    def on_list_plates(self):
        list_plates()


@app.route('/')
def index():
    return render_template('index.html')


# Serve a file from a specific path
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        # Change 'path_to_files' to the directory where your files are stored
        filepath = os.path.join(app.config['ZIP_FOLDER'], filename)
        return send_file(filepath, as_attachment=True)
    except FileNotFoundError:
        return "File not found", 404


########## DATA HANDLING AND COMPUTE FUNCTIONS ##########

def allowed_file(filename):
    """
    Checks if the uploaded file is an allowed extension.
    :param filename: Full filename of the uploaded file
    :return: True if the file is an allowed extension, False otherwise.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def plate_allowed_file(filename):
    """
    Checks if the uploaded file is an allowed extension.
    :param filename: Full filename of the uploaded file
    :return: True if the file is an allowed extension, False otherwise.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['PLATE_ALLOWED_EXTENSIONS']


def get_inventory():
    """
    Gets all inventory items from the used cargo folder and sends them to the client.
    """
    # TODO: also connect the above with 'pre-made' plates from the server defaults
    all_inventory_items = []

    # Iterate through all .xlsx files in the directory to get inventory items
    for filename in os.listdir(app.config['PLATE_FOLDER']):
        if filename.endswith('.xlsx'):
            shortened_filename = filename[:-5]
            file_path = os.path.join(app.config['PLATE_FOLDER'], shortened_filename)
            # Run getInventory on the current file and extend the results to the all_inventory_items list
            inventory_items = cargo_to_inventory(file_path, app.config['PLATE_FOLDER'])
            all_inventory_items.extend(inventory_items)

    emit('inventory_sent', all_inventory_items)


def upload_and_import_design(data):
    """
    Receives an imported design file (xlsx) from the frontend, which is saved to the server directory, imported into
    a megastructure and the contents sent back to the frontend for display.
    """
    file = data['file']
    filename = 'crisscross_design.xlsx'
    if file and allowed_file(filename):
        try:
            with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'wb') as f:
                f.write(file['data'])
            emit('upload_response', {'message': 'File successfully uploaded'})
            print('File successfully uploaded')
        except Exception as e:
            emit('upload_response', {'message': f"An error occurred while saving the file: {str(e)}"})
            print(f"An error occurred while saving the file: {str(e)}")
    else:
        emit('upload_response', {'message': 'File type not allowed'})
        print('File type not allowed')

    print('Design will be imported')
    crisscross_design_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    print(crisscross_design_path)

    crisscross_megastructure = Megastructure(import_design_file=crisscross_design_path)
    seed_dict = {}
    handle_dict = {}
    cargo_dict = {}

    if crisscross_megastructure.seed_array is not None:
        seed_dict = positional_2d_array_and_layer_to_dict(crisscross_megastructure.seed_array[1],
                                                          crisscross_megastructure.seed_array[0])

    slat_dict = positional_3d_array_to_dict(crisscross_megastructure.slat_array)

    if crisscross_megastructure.handle_arrays is not None:
        handle_dict = positional_3d_array_to_dict(crisscross_megastructure.handle_arrays)

    if crisscross_megastructure.cargo_dict is not None:
        cargo_dict = cargo_dict_to_formatted(crisscross_megastructure.cargo_dict)

    emit('design_imported', [seed_dict, slat_dict, cargo_dict, handle_dict])

    # TODO: Add import of handle configs


def generate_handles(data):
    crisscross_dict = data[0]
    handle_configs = data[1]
    handle_rounds = int(data[2])

    seed_array, slat_array, cargo_dict, handle_array = convert_design_dictionaries_into_arrays({},
                                                                                               crisscross_dict[1],
                                                                                               {},
                                                                                               {},
                                                                                               handle_rounds,
                                                                                               False,
                                                                                               False)

    handle_dict = positional_3d_array_to_dict(handle_array)
    converted_handle_dict = convert_np_to_py(handle_dict)
    emit('handles_sent', converted_handle_dict)


def package_and_export_megastructure(data):
    """
    Given the entire set of data (slats, handles, cargo, seeds) from the frontend, this function packages the entire
    input into a Megastructure class, generates the design graphics and echo commands, and exports the design for the
    user to download.
    """

    clear_folder_contents(app.config['OUTPUT_FOLDER'])  # TODO: this will not work in a production environment

    # assigns the data to the appropriate variables
    seed_dict, slat_dict, cargo_dict, handle_dict = data[0]
    handle_configs = data[1]
    use_display_handles, generate_graphics, generate_echo = data[2]

    # converts the handle configurations to the Megastructure string format
    formatted_layer_handle_orientations = convert_dict_handle_orientations_to_string(handle_configs)

    # generates the design arrays from the provided dictionaries
    seed_array, slat_array, cargo_dict, handle_array = convert_design_dictionaries_into_arrays(seed_dict,
                                                                                               slat_dict,
                                                                                               cargo_dict,
                                                                                               handle_dict,
                                                                                               100, # TODO: make this user-selectable and add evolution system...
                                                                                               use_display_handles)

    megastructure = combine_megastructure_arrays(seed_array, slat_array, cargo_dict, handle_array,
                                                 formatted_layer_handle_orientations)

    if generate_graphics:
        if platform.system() == 'Darwin':
            gen_3d = False
        else:
            gen_3d = True
        megastructure.create_standard_graphical_report(os.path.join(app.config['OUTPUT_FOLDER'], 'Design Graphics'),
                                                       generate_3d_video=gen_3d, colormap='Set1',
                                                       cargo_colormap='Paired')
        # TODO: cannot generate 3D graphics on mac os due to threading issues....

    if generate_echo:
        core_plate, crisscross_antihandle_y_plates, crisscross_handle_x_plates, seed_plate, center_seed_plate, combined_seed_plate = get_standard_plates()
        megastructure.patch_placeholder_handles(
            [crisscross_handle_x_plates, crisscross_antihandle_y_plates, combined_seed_plate],
            ['Assembly-Handles', 'Assembly-AntiHandles', 'Seed'])
        megastructure.patch_control_handles(core_plate)
        convert_slats_into_echo_commands(megastructure.slats, 'crisscross_design_plate',
                                         app.config['OUTPUT_FOLDER'], 'all_echo_commands_with_crisscross_design.csv',
                                         default_transfer_volume=100)

    megastructure.export_design('full_design.xlsx', app.config['OUTPUT_FOLDER'])

    zip_folder_to_disk(app.config['OUTPUT_FOLDER'], os.path.join(app.config['ZIP_FOLDER'], 'outputs.zip'))

    emit('megastructure_output_ready_to_download')


def save_file_to_plate_folder(data):
    """
    Save uploaded file to the upload folder.
    :param data: Dictionary containing file data
    :return: None
    """
    file = data['file']
    filename = secure_filename(file['filename'])
    if file and plate_allowed_file(filename):
        try:
            with open(os.path.join(app.config['PLATE_FOLDER'], filename), 'wb') as f:
                f.write(file['data'])
            emit('plate_upload_response', {'message': f'File {filename} successfully uploaded'})
            print(f'File {filename} successfully uploaded')
        except Exception as e:
            emit('plate_upload_response', {'message': f"An error occurred while saving the file {filename}: {str(e)}"})
            print(f"An error occurred while saving the file {filename}: {str(e)}")
    else:
        emit('plate_upload_response', {'message': f'File type {filename} not allowed'})
        print(f'File type {filename} not allowed')


def list_plates():
    files = os.listdir(app.config['PLATE_FOLDER'])
    emit('list_plates_response', files)



