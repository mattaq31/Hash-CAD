# TODO: consider naming the 'templates' folder to 'webpages' to be more descriptive
# TODO: consider renaming static folder to 'frontend' to be more descriptive, and to include the HTML there too

#Basic flask imports
from flask import Flask, render_template, send_from_directory, send_file
from flask_socketio import SocketIO
from flask_socketio import send, emit

# For file uploads
from werkzeug.utils import secure_filename
import os
from os.path import join

# For data handling
import numpy as np
from crisscross.helper_functions import create_dir_if_empty
from server_helper_functions import (slat_dict_to_array, cargo_dict_to_array,
                                     array_to_dict, cargo_to_inventory, convert_np_to_py,
                                     getDriverNames, break_array_by_plates)

#For generating handles
from crisscross.core_functions.megastructures import Megastructure
from crisscross.plate_mapping import get_plateclass
from crisscross.helper_functions.plate_constants import (slat_core, core_plate_folder, crisscross_h5_handle_plates,
                                                         crisscross_h2_handle_plates, assembly_handle_folder,
                                                         seed_plug_plate_center, cargo_plate_folder, simpsons_mixplate_antihandles,
                                                         nelson_quimby_antihandles, seed_plug_plate_corner)
from crisscross.core_functions.hamming_functions import generate_handle_set_and_optimize, multi_rule_hamming


app = Flask(__name__)

#app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Directory to save uploaded files
app.config['USED_CARGO_FOLDER'] = 'used-cargo-plates/'  # Directory to save uploaded files
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'npz'}  # Allowed file extensions
socketio = SocketIO(app, max_http_buffer_size=100 * 1024 * 1024) #Set max transfer size 100MB

# Ensure the upload directory exists
create_dir_if_empty(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    """
    Checks if the uploaded file is an allowed extension.
    :param filename: Full filename of the uploaded file
    :return: True if the file is an allowed extension, False otherwise.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    return render_template('index.html')

# Serve a file from a specific path
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        # Change 'path_to_files' to the directory where your files are stored
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        return send_file(filepath, as_attachment=True)
    except FileNotFoundError:
        return "File not found", 404



@socketio.on('get_inventory')
def get_inventory(folder_path, plate_driver_dict):

    all_inventory_items = []

    for filename in plate_driver_dict.keys():
        shortened_filename = filename[:-5]
        file_path = os.path.join(folder_path, shortened_filename)
        # Run getInventory on the current file and extend the results to the all_inventory_items list
        inventory_items = cargo_to_inventory(plate_driver_dict[filename], file_path, folder_path)
        all_inventory_items.extend(inventory_items)

    # Iterate through all .xlsx files in the directory to get inventory items
    #for filename in os.listdir(folder_path):
    #    if filename.endswith('.xlsx'):
    #        if filename in plate_driver_dict:
    #            shortened_filename = filename[:-5]
    #            file_path = os.path.join(folder_path, shortened_filename)
    #            # Run getInventory on the current file and extend the results to the all_inventory_items list
    #            inventory_items = cargo_to_inventory(plate_driver_dict[filename], file_path, folder_path)
    #            all_inventory_items.extend(inventory_items)

    emit('inventory_sent',all_inventory_items)

@socketio.on('get_drivers')
def get_drivers(folder_path):
    # Get inventory drivers
    base_directory = os.path.abspath(join(folder_path, os.path.pardir, os.path.pardir))
    functions_dir = os.path.join(base_directory, 'crisscross', 'plate_mapping')
    all_inventory_drivers = getDriverNames(functions_dir)

    # Now get a list of the plates:
    plate_names = []
    for filename in os.listdir(folder_path):
        plate_names.append(filename)


    emit('drivers_sent',[all_inventory_drivers, plate_names])



# TODO: consider giving this a more descriptive name - what type of file is being uploaded?
@socketio.on('upload_file')
def save_file_to_uploads(data):
    """
    TODO: fill in
    :param data:
    :return:
    """
    file = data['file']
    filename = 'crisscross_design.npz' #secure_filename(file['filename'])
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
    crisscross_design_file = np.load(crisscross_design_path, allow_pickle=True)
    slat_array = crisscross_design_file['slat_array']
    cargo_array = crisscross_design_file['cargo_array']

    slat_dict = {}
    cargo_dict = {}

    if(slat_array.ndim == 3):
        slat_dict = array_to_dict(slat_array)

    if (cargo_array.ndim == 3):
        cargo_dict = array_to_dict(cargo_array)

    emit('design_imported', [slat_dict, cargo_dict])


# TODO: make function names more descriptive
@socketio.on('design_saved')
def save_crisscross_design(crisscross_dict):
    """
    TODO: fill in
    :param crisscross_dict:
    :return:
    """
    print('Design has been saved')
    # TODO: consider saving file in a human-readable format like toml
    slat_array = ()
    cargo_array = ()

    if(crisscross_dict[0]):
        slat_array = slat_dict_to_array(crisscross_dict[0])

    if (crisscross_dict[1]):
        cargo_array = cargo_dict_to_array(crisscross_dict[1])

    crisscross_design_path = os.path.join(app.config['UPLOAD_FOLDER'], 'crisscross_design.npz')

    # Save the arrays to a .npz file (including multiple numpy arrays!)
    np.savez(crisscross_design_path, slat_array=slat_array, cargo_array=cargo_array)


@socketio.on('generate_handles')
def generate_handles(crisscross_dict):
    slat_array = ()
    if (crisscross_dict[0]):
        slat_array = slat_dict_to_array(crisscross_dict[0], trim_offset=False)

    # Generate empty handle array
    handle_array = generate_handle_set_and_optimize(slat_array, unique_sequences=32, slat_length=32, max_rounds=5,
                                     split_sequence_handles=False, universal_hamming=True, layer_hamming=False,
                                     group_hamming=None, metric_to_optimize='Universal')

    # Generates plate dictionaries from provided files
    crisscross_antihandle_y_plates = get_plateclass('CrisscrossHandlePlates',
                                                    crisscross_h5_handle_plates[3:] + crisscross_h2_handle_plates,
                                                    assembly_handle_folder, plate_slat_sides=[5, 5, 5, 2, 2, 2])
    crisscross_handle_x_plates = get_plateclass('CrisscrossHandlePlates',
                                                crisscross_h5_handle_plates[0:3],
                                                assembly_handle_folder, plate_slat_sides=[5, 5, 5])

    # prepares the actual full megastructure here
    crisscross_megastructure = Megastructure(slat_array, None, connection_angle='90')
    crisscross_megastructure.assign_crisscross_handles(handle_array, crisscross_handle_x_plates,
                                                       crisscross_antihandle_y_plates)
    handle_dict = array_to_dict(handle_array)

    converted_handle_dict = convert_np_to_py(handle_dict)

    print(converted_handle_dict)
    emit('handles_sent', converted_handle_dict)

@socketio.on('generate_megastructures')
def generate_megastructure(crisscross_dict, plateDriverMap):


    slat_array = ()
    cargo_array = ()

    if (crisscross_dict[0]):
        slat_array = slat_dict_to_array(crisscross_dict[0], trim_offset=True)

    if (crisscross_dict[1]):
        cargo_array = cargo_dict_to_array(crisscross_dict[1], trim_offset=True, slat_grid_dict=crisscross_dict[0])

    #Generate empty handle array
    handle_array = generate_handle_set_and_optimize(slat_array, unique_sequences=32, slat_length=32, max_rounds=5,
                                     split_sequence_handles=False, universal_hamming=True, layer_hamming=False,
                                     group_hamming=None, metric_to_optimize='Universal')

    #Get plates!

    # Generates crisscross handle plate dictionaries from provided files
    crisscross_antihandle_y_plates = get_plateclass('CrisscrossHandlePlates',
                                                    crisscross_h5_handle_plates[3:] + crisscross_h2_handle_plates,
                                                    assembly_handle_folder, plate_slat_sides=[5, 5, 5, 2, 2, 2])
    crisscross_handle_x_plates = get_plateclass('CrisscrossHandlePlates',
                                                crisscross_h5_handle_plates[0:3],
                                                assembly_handle_folder, plate_slat_sides=[5, 5, 5])

    # prepares the actual full megastructure here
    crisscross_megastructure = Megastructure(slat_array, None, connection_angle='90')
    crisscross_megastructure.assign_crisscross_handles(handle_array, crisscross_handle_x_plates,
                                                       crisscross_antihandle_y_plates)

    # Add cargo
    if(cargo_array.size != 0):
        # Iterate over layers:
        layer_counter = 1
        for layer in range(cargo_array.shape[2]):
            tmp_layer_array = cargo_array[:, :, layer]
            tmp_layer_plate_dict = break_array_by_plates(tmp_layer_array)
            for plate, cargo_by_plate in tmp_layer_plate_dict.items():
                if(plate != ''):
                    plate_file = plate + ".xlsx"
                    plate_driver_name = plateDriverMap[plate_file]
                    plate_folder = app.config['USED_CARGO_FOLDER']


                    plate_class = get_plateclass(plate_driver_name, plate, plate_folder)
                    crisscross_megastructure.assign_cargo_handles(cargo_by_plate, plate_class,
                                                                  layer=layer_counter, requested_handle_orientation=2)
            layer_counter += 1

        core_plate = get_plateclass('ControlPlate', slat_core, core_plate_folder)
        crisscross_megastructure.patch_control_handles(core_plate)

    crisscross_megastructure.create_standard_graphical_report(os.path.join(app.config['UPLOAD_FOLDER'], 'Design Graphics'),
                                                              colormap='Set1', cargo_colormap='Paired')


if __name__ == '__main__':
    socketio.run(app, allow_unsafe_werkzeug=True)  # TODO: what does the allow_unsafe_werkzeug parameter do?

    #Note: terminal threw an error and said to set allow_unsafe_werkzeug=True in order to run program. Not entirely sure why...
