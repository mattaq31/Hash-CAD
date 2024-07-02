# TODO: consider naming the 'templates' folder to 'webpages' to be more descriptive
# TODO: consider renaming static folder to 'frontend' to be more descriptive, and to include the HTML there too

#Basic flask imports
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_socketio import send, emit

# For file uploads
from werkzeug.utils import secure_filename
import os

# For data handling
import numpy as np
from crisscross.helper_functions import create_dir_if_empty
from server_helper_functions import slat_dict_to_array, cargo_dict_to_array,array_to_dict



app = Flask(__name__)

#app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Directory to save uploaded files
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'npz'}  # Allowed file extensions
socketio = SocketIO(app)

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


# TODO: consider giving this a more descriptive name - what type of file is being uploaded?
@socketio.on('upload_file')
def save_file_to_uploads(data):
    """
    TODO: fill in
    :param data:
    :return:
    """
    file = data['file']
    filename = secure_filename(file['filename'])
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
    slat_array = slat_dict_to_array(crisscross_dict[0])
    cargo_array = cargo_dict_to_array(crisscross_dict[1])

    crisscross_design_path = os.path.join(app.config['UPLOAD_FOLDER'], 'crisscross_design.npz')

    # Save the arrays to a .npz file (including multiple numpy arrays!)
    np.savez(crisscross_design_path, slat_array=slat_array, cargo_array=cargo_array)


@socketio.on('design_import_request')
def load_crisscross_design():
    """
    TODO: fill in
    :return:
    """
    print('Design will be imported')
    crisscross_design_path = os.path.join(app.config['UPLOAD_FOLDER'], 'crisscross_design.npz')
    crisscross_design_file = np.load(crisscross_design_path)
    slat_array = crisscross_design_file['slat_array']
    cargo_array = crisscross_design_file['cargo_array']

    slat_dict = array_to_dict(slat_array)
    cargo_dict = array_to_dict(cargo_array)
    emit('design import sent', [slat_dict, cargo_dict])


if __name__ == '__main__':
    socketio.run(app, allow_unsafe_werkzeug=True)  # TODO: what does the allow_unsafe_werkzeug parameter do?

    #Note: terminal threw an error and said to set allow_unsafe_werkzeug=True in order to run program. Not entirely sure why...
