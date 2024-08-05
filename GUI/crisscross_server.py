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
                                     clear_folder_contents,
                                     generate_formatted_orientations,
                                     generate_design_arrays,
                                     gen_megastructure,
                                     import_megastructure)



app = Flask(__name__)

#app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Directory to save uploaded files
app.config['OUTPUT_FOLDER'] = 'outputs/'
app.config['USED_CARGO_FOLDER'] = 'used-cargo-plates/'  # Directory to save uploaded files
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'npz', 'xlsx'}  # Allowed file extensions
app.config['PLATE_ALLOWED_EXTENSIONS'] = {'xlsx'}  # Allowed file extensions

socketio = SocketIO(app, max_http_buffer_size=100 * 1024 * 1024) #Set max transfer size 100MB

# Ensure the upload directory exists
create_dir_if_empty(app.config['UPLOAD_FOLDER'])


import sys
class DualStreamHandler:
    def __init__(self):
        self._stdout = sys.stdout
        self._stderr = sys.stderr

    def write(self, message):
        if isinstance(message, bytes):
            message = message.decode('utf-8')
        if message and not message.isspace():
            if not message.endswith('\n'):
                message += '\n'
            self._stdout.write(message)
            self._stdout.flush()
            socketio.emit('console', {'data': message})

    def flush(self):
        self._stdout.flush()

# Replace sys.stdout and sys.stderr with the dual handler
sys.stdout = DualStreamHandler()
sys.stderr = DualStreamHandler()

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
def get_inventory():

    all_inventory_items = []

    # Iterate through all .xlsx files in the directory to get inventory items
    for filename in os.listdir(app.config['USED_CARGO_FOLDER']):
        if filename.endswith('.xlsx'):
            shortened_filename = filename[:-5]
            file_path = os.path.join(app.config['USED_CARGO_FOLDER'], shortened_filename)
            # Run getInventory on the current file and extend the results to the all_inventory_items list
            inventory_items = cargo_to_inventory(file_path, app.config['USED_CARGO_FOLDER'])
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
    filename = 'crisscross_design.xlsx' #'crisscross_design.npz' #secure_filename(file['filename'])
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

    import_megastructure(crisscross_design_path)


    '''
    crisscross_design_file = np.load(crisscross_design_path, allow_pickle=True)
    seed_array = crisscross_design_file['seed_array']
    slat_array = crisscross_design_file['slat_array']
    cargo_dict = crisscross_design_file['cargo_dict'].item()
    handle_dict = crisscross_design_file['handle_dict'].item()

    seed_dict = {}
    slat_dict = {}

    if(seed_array.ndim == 3):
        seed_dict = array_to_dict(seed_array)

    if(slat_array.ndim == 3):
        slat_dict = array_to_dict(slat_array)

    if(not(cargo_dict)):
        cargo_dict = {}

    if (not (handle_dict)):
        handle_dict = {}
    


    emit('design_imported', [seed_dict, slat_dict, cargo_dict, handle_dict])'''





'''
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
    handle_dict = {}

    if (crisscross_dict[0]):
        seed_array = seed_dict_to_array(crisscross_dict[0])

    if(crisscross_dict[1]):
        slat_array = slat_dict_to_array(crisscross_dict[1])

    if (crisscross_dict[2]):
        cargo_dict = crisscross_dict[2]

    if (crisscross_dict[3]):
        handle_dict = crisscross_dict[3]



    crisscross_design_path = os.path.join(app.config['UPLOAD_FOLDER'], 'crisscross_design.npz')

    # Save the arrays to a .npz file (including multiple numpy arrays!)
    np.savez(crisscross_design_path,
             seed_array=np.array(seed_array),
             slat_array=np.array(slat_array),
             cargo_dict=cargo_dict,
             handle_dict=handle_dict)

    emit('saved_design_ready_to_download')
'''

@socketio.on('generate_handles')
def generate_handles(data):
    crisscross_dict = data[0]
    handle_configs = data[1]
    handle_rounds = int(data[2])

    seed_array, slat_array, cargo_dict, handle_array = generate_design_arrays({},
                                                                              crisscross_dict[1],
                                                                              {},
                                                                              {},
                                                                              handle_rounds,
                                                                              False,
                                                                              False)

    handle_dict = array_to_dict(handle_array)
    converted_handle_dict = convert_np_to_py(handle_dict)
    emit('handles_sent', converted_handle_dict)

@socketio.on('generate_megastructures')
def generate_megastructure(data):
    clear_folder_contents(app.config['OUTPUT_FOLDER'])

    crisscross_dict = data[0]
    handle_configs = data[1]
    general_configs = data[2]

    old_handles = general_configs[0]
    generate_graphics = general_configs[1]
    generate_echo = general_configs[2]

    formatted_orientations = generate_formatted_orientations(handle_configs)
    print(formatted_orientations)

    seed_array, slat_array, cargo_dict, handle_array = generate_design_arrays(crisscross_dict[0],
                                                                              crisscross_dict[1],
                                                                              crisscross_dict[2],
                                                                              crisscross_dict[3],
                                                                              10,
                                                                              old_handles)

    crisscross_megastructure = gen_megastructure(seed_array,
                                                 slat_array,
                                                 cargo_dict,
                                                 handle_array,
                                                 formatted_orientations,
                                                 generate_graphics,
                                                 generate_echo,
                                                 True,
                                                 app.config['USED_CARGO_FOLDER'],
                                                 app.config['OUTPUT_FOLDER'],
                                                 app.config['UPLOAD_FOLDER'])

    emit('megastructure_output_ready_to_download')


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
