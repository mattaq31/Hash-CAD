# TODO: consider naming the 'templates' folder to 'webpages' to be more descriptive
# TODO: consider renaming static folder to 'frontend' to be more descriptive, and to include the HTML there too

#Basic flask imports
from flask import Flask, render_template, send_file
from flask_socketio import SocketIO
from flask_socketio import emit

# For file uploads
from werkzeug.utils import secure_filename
import os

# For data handling
import numpy as np
from crisscross.helper_functions import create_dir_if_empty
from server_helper_functions import (seed_dict_to_array, slat_dict_to_array,
                                     array_to_dict,
                                     cargo_to_inventory, convert_np_to_py,
                                     break_dict_by_plates,
                                     format_dict)

#For generating handles
from crisscross.core_functions.megastructures import Megastructure
from crisscross.plate_mapping import get_plateclass
from crisscross.helper_functions.plate_constants import (slat_core, core_plate_folder, crisscross_h5_handle_plates,
                                                         crisscross_h2_handle_plates, assembly_handle_folder,
                                                         seed_plug_plate_corner)
from crisscross.core_functions.hamming_functions import generate_handle_set_and_optimize
from crisscross.core_functions.megastructure_composition import convert_slats_into_echo_commands


app = Flask(__name__)

#app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Directory to save uploaded files
app.config['OUTPUT_FOLDER'] = 'outputs/'
app.config['USED_CARGO_FOLDER'] = 'used-cargo-plates/'  # Directory to save uploaded files
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'npz'}  # Allowed file extensions
app.config['PLATE_ALLOWED_EXTENSIONS'] = {'xlsx'}  # Allowed file extensions

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

def plate_allowed_file(filename):
    """
    Checks if the uploaded file is an allowed extension.
    :param filename: Full filename of the uploaded file
    :return: True if the file is an allowed extension, False otherwise.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['PLATE_ALLOWED_EXTENSIONS']


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
def get_inventory(folder_path):

    all_inventory_items = []

    # Iterate through all .xlsx files in the directory to get inventory items
    for filename in os.listdir(folder_path):
        if filename.endswith('.xlsx'):
            shortened_filename = filename[:-5]
            file_path = os.path.join(folder_path, shortened_filename)
            # Run getInventory on the current file and extend the results to the all_inventory_items list
            inventory_items = cargo_to_inventory(file_path, folder_path)
            all_inventory_items.extend(inventory_items)

    emit('inventory_sent',all_inventory_items)




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
    print(crisscross_design_path)
    crisscross_design_file = np.load(crisscross_design_path, allow_pickle=True)
    seed_array = crisscross_design_file['seed_array']
    slat_array = crisscross_design_file['slat_array']
    cargo_dict = crisscross_design_file['cargo_dict'].item()

    seed_dict = {}
    slat_dict = {}

    if(seed_array.ndim == 3):
        seed_dict = array_to_dict(seed_array)

    if(slat_array.ndim == 3):
        slat_dict = array_to_dict(slat_array)

    if(not(cargo_dict)):
        cargo_dict = {}


    emit('design_imported', [seed_dict, slat_dict, cargo_dict])


# TODO: make function names more descriptive
@socketio.on('design_to_backend_for_download')
def save_crisscross_design(crisscross_dict):
    """
    TODO: fill in
    :param crisscross_dict:
    :return:
    """
    print('Design has been saved')
    # TODO: consider saving file in a human-readable format like toml
    seed_array = ()
    slat_array = ()
    cargo_dict = {}
    #top_cargo_array = ()
    #bottom_cargo_array = ()

    if (crisscross_dict[0]):
        seed_array = seed_dict_to_array(crisscross_dict[0])

    if(crisscross_dict[1]):
        slat_array = slat_dict_to_array(crisscross_dict[1])

    if (crisscross_dict[2]):
        cargo_dict = crisscross_dict[2]
        #bottom_cargo_array = cargo_dict_to_array(crisscross_dict[2])

    #if (crisscross_dict[3]):
    #    top_cargo_array = cargo_dict_to_array(crisscross_dict[3])



    crisscross_design_path = os.path.join(app.config['UPLOAD_FOLDER'], 'crisscross_design.npz')

    # Save the arrays to a .npz file (including multiple numpy arrays!)
    np.savez(crisscross_design_path,
             seed_array=np.array(seed_array),
             slat_array=np.array(slat_array),
             cargo_dict=cargo_dict)

    emit('saved_design_ready_to_download')


@socketio.on('generate_handles')
def generate_handles(data):
    crisscross_dict = data[0]
    handle_configs = data[1]

    layer_interface_orientation = []
    for orientation in handle_configs.values():
        layer_interface_orientation.append((int(orientation[0]), int(orientation[1])))

    # Now change this layer_interface_orientation array into the proper format: ie [2, (5, 2), (5, 2), 5]
    first_orientation = layer_interface_orientation[0][0]
    last_orientation = layer_interface_orientation[-1][1]
    middle_orientations = [(layer_interface_orientation[i][1], layer_interface_orientation[i + 1][0])
                           for i in range(len(layer_interface_orientation) - 1)]
    formatted_orientations = [first_orientation] + middle_orientations + [last_orientation]

    print(formatted_orientations)



    slat_array = ()
    if (crisscross_dict[1]):
        slat_array = slat_dict_to_array(crisscross_dict[1], trim_offset=False)

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
    crisscross_megastructure = Megastructure(slat_array, formatted_orientations, connection_angle='90')
    crisscross_megastructure.assign_crisscross_handles(handle_array, crisscross_handle_x_plates,
                                                       crisscross_antihandle_y_plates)
    handle_dict = array_to_dict(handle_array)

    converted_handle_dict = convert_np_to_py(handle_dict)

    print(converted_handle_dict)
    emit('handles_sent', converted_handle_dict)

@socketio.on('generate_megastructures')
def generate_megastructure(data):
    crisscross_dict = data[0]
    handle_configs = data[1]

    layer_interface_orientation = []
    for orientation in handle_configs.values():
        layer_interface_orientation.append( (int(orientation[0]), int(orientation[1])) )

    #Now change this layer_interface_orientation array into the proper format: ie [2, (5, 2), (5, 2), 5]
    first_orientation = layer_interface_orientation[0][0]
    last_orientation = layer_interface_orientation[-1][1]
    middle_orientations = [(layer_interface_orientation[i][1], layer_interface_orientation[i+1][0])
                           for i in range(len(layer_interface_orientation)-1)]
    formatted_orientations = [first_orientation] + middle_orientations + [last_orientation]

    print(formatted_orientations)


    seed_array = np.array([])
    slat_array = ()
    cargo_dict = {}

    if (crisscross_dict[0]):
        seed_array = seed_dict_to_array(crisscross_dict[0], trim_offset=True, slat_grid_dict=crisscross_dict[1])

    if (crisscross_dict[1]):
        slat_array = slat_dict_to_array(crisscross_dict[1], trim_offset=True)

    if (crisscross_dict[2]):
        cargo_dict = format_dict(crisscross_dict[2], trim=True, reference_slat_dict=crisscross_dict[1])

    #Generate empty handle array
    handle_array = generate_handle_set_and_optimize(slat_array, unique_sequences=32, slat_length=32, max_rounds=5,
                                     split_sequence_handles=False, universal_hamming=True, layer_hamming=False,
                                     group_hamming=None, metric_to_optimize='Universal')

    # Generates crisscross handle plate dictionaries from provided files
    crisscross_antihandle_y_plates = get_plateclass('CrisscrossHandlePlates',
                                                    crisscross_h5_handle_plates[3:] + crisscross_h2_handle_plates,
                                                    assembly_handle_folder, plate_slat_sides=[5, 5, 5, 2, 2, 2])
    crisscross_handle_x_plates = get_plateclass('CrisscrossHandlePlates',
                                                crisscross_h5_handle_plates[0:3],
                                                assembly_handle_folder, plate_slat_sides=[5, 5, 5])

    edge_seed_plate = get_plateclass('CornerSeedPlugPlate', seed_plug_plate_corner, core_plate_folder)

    # prepares the actual full megastructure here
    crisscross_megastructure = Megastructure(slat_array, formatted_orientations, connection_angle='90')
    crisscross_megastructure.assign_crisscross_handles(handle_array, crisscross_handle_x_plates,
                                                       crisscross_antihandle_y_plates)

    #Add seeds
    if (seed_array.size != 0):
        # Iterate over layers:
        layer_counter = 0
        for layer in range(seed_array.shape[2]):
            if(np.any(seed_array[:,:,layer])):
                crisscross_megastructure.assign_seed_handles(seed_array[:, :, layer], edge_seed_plate, layer_id=layer_counter + 1)

    # Add cargo
    if(crisscross_dict[2]):
        cargo_by_plate = break_dict_by_plates(cargo_dict)
        for plate, single_plate_cargo in cargo_by_plate.items():
            if (plate != ''):
                plate_folder = app.config['USED_CARGO_FOLDER']
                plate = get_plateclass('GenericPlate', plate, plate_folder)
                crisscross_megastructure.assign_cargo_handles_with_dict(single_plate_cargo, plate)


    core_plate = get_plateclass('ControlPlate', slat_core, core_plate_folder)
    crisscross_megastructure.patch_control_handles(core_plate)

    crisscross_megastructure.create_standard_graphical_report(os.path.join(app.config['OUTPUT_FOLDER'], 'Design Graphics'),
                                                              colormap='Set1', cargo_colormap='Paired')

    convert_slats_into_echo_commands(crisscross_megastructure.slats, 'crisscross_design_plate',
                                     app.config['OUTPUT_FOLDER'],'all_echo_commands_with_crisscross_design.csv',
                                     transfer_volume=100)

@socketio.on('upload_plates')
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
            with open(os.path.join(app.config['USED_CARGO_FOLDER'], filename), 'wb') as f:
                f.write(file['data'])
            emit('plate_upload_response', {'message': f'File {filename} successfully uploaded'})
            print(f'File {filename} successfully uploaded')
        except Exception as e:
            emit('plate_upload_response', {'message': f"An error occurred while saving the file {filename}: {str(e)}"})
            print(f"An error occurred while saving the file {filename}: {str(e)}")
    else:
        emit('plate_upload_response', {'message': f'File type {filename} not allowed'})
        print(f'File type {filename} not allowed')

@socketio.on('list_plates')
def list_plates():
    files = os.listdir(app.config['USED_CARGO_FOLDER'])
    emit('list_plates_response', files)


if __name__ == '__main__':
    socketio.run(app, allow_unsafe_werkzeug=True)  # TODO: what does the allow_unsafe_werkzeug parameter do?

    #Note: terminal threw an error and said to set allow_unsafe_werkzeug=True in order to run program. Not entirely sure why...
