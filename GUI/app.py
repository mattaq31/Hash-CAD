# TODO: clean up imports that are not in use
# TODO: change all function arguments to lowercase, to match normal python convention
# TODO: delete the package.json and package-lock.json files - we are not using node.js anymore
# TODO: do not upload any npyarrays to the repo.  Add a clause in the gitignore to ignore these.
# TODO: alternatively, ignore the uploads folder entirely.
# TODO: consider naming the 'templates' folder to 'webpages' to be more descriptive
# TODO: consider renaming app.py to a more descriptive name like 'crisscross_server.py'
# TODO: consider renaming static folder to 'frontend' to be more descriptive, and to include the HTML there too

from flask import Flask, abort, render_template

from markupsafe import escape
from flask_socketio import SocketIO
from flask_socketio import send, emit

# For file uploads
from flask import request, redirect, url_for
from werkzeug.utils import secure_filename
import os

# For data handling
import numpy as np

from crisscross.helper_functions import create_dir_if_empty

app = Flask(__name__)

# TODO: what is this key for?  add a comment for now if not in use
app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Directory to save uploaded files
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}  # Allowed file extensions
socketio = SocketIO(app)

# Ensure the upload directory exists
create_dir_if_empty(app.config['UPLOAD_FOLDER'])


# TODO: consider moving all these small functions not directly related to flask to a separate file
# Functions for file upload:
def allowed_file(filename):
    """
    TODO: fill in
    :param filename:
    :return:
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def slatDictToArray(gridDict):
    """
    TODO: fill in
    :param gridDict:
    :return:
    """
    # Parse the keys to determine the dimensions
    max_x = max(int(key.split(',')[0]) for key in gridDict.keys()) + 1
    max_y = max(int(key.split(',')[1]) for key in gridDict.keys()) + 1
    max_layer = max(int(key.split(',')[2]) for key in gridDict.keys()) + 1

    # Initialize the array
    array = np.zeros((max_x, max_y, max_layer))

    # Populate the array
    for key, slatId in gridDict.items():
        x, y, layer = map(int, key.split(','))
        array[x, y, layer] = slatId

    return array


def cargoDictToArray(gridDict):
    """
    TODO: fill in
    :param gridDict:
    :return:
    """
    if gridDict:  # TODO: if there is no gridDict then this function should never be called - extract the logic out from this function
        # Parse the keys to determine the dimensions
        max_x = max(int(key.split(',')[0]) for key in gridDict.keys()) + 1
        max_y = max(int(key.split(',')[1]) for key in gridDict.keys()) + 1
        max_layer = max(int(key.split(',')[2]) for key in gridDict.keys()) + 1

        # Initialize the array
        array = np.zeros((max_x, max_y, max_layer))

        # Populate the array
        for key, cargoType in gridDict.items():
            x, y, layer = map(int, key.split(','))
            array[x, y, layer] = cargoType

        return array


def arrayToDict(array):
    """
    TODO: fill in
    :param array:
    :return:
    """
    if (array.shape != ()): # TODO: this function should not be called if the array is empty - extract the logic out from this function
        # Convert numpy array to a list of dictionaries
        dict = {}
        x_dim, y_dim, layer_dim = array.shape
        for x in range(x_dim):
            for y in range(y_dim):
                for layer in range(layer_dim):
                    entry = array[x, y, layer]
                    if entry != 0:
                        dict[f'{x},{y},{layer}'] = entry
        return dict


@app.route('/')
def index():
    return render_template('index.html')


# TODO: consider giving this a more descriptive name - what type of file is being uploaded?
@socketio.on('upload_file')
def handle_upload_file(data):
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


# TODO: decide on a convention for the socket names - either underscores or no underscores (I prefer underscores)
# TODO: make function names more descriptive
@socketio.on('design saved')
def handle_my_custom_event(crisscrossDict):
    """
    TODO: fill in
    :param crisscrossDict:
    :return:
    """
    print('Design has been saved')
    # TODO: consider saving file in a human-readable format like toml
    slatArray = slatDictToArray(crisscrossDict[0])
    cargoArray = cargoDictToArray(crisscrossDict[1])

    # Save the arrays to a .npy file
    # TODO: these should be saved to the uploads folder and not at the root
    np.save('slatArray.npy', slatArray)
    np.save('cargoArray.npy', cargoArray)


@socketio.on('design import request')
def handle_my_custom_event():
    """
    TODO: fill in
    :return:
    """
    print('Design will be imported')
    slatArray = np.load('slatArray.npy', allow_pickle=True)
    cargoArray = np.load('cargoArray.npy', allow_pickle=True)
    slatDict = arrayToDict(slatArray)
    cargoDict = arrayToDict(cargoArray)
    emit('design import sent', [slatDict, cargoDict])


# TODO: prefer removing fully commented functions from committed code - move to a scratch folder instead
# @socketio.on('my layer removed event')
# def handle_my_custom_event(json):
#    print('Layer removed: ' + str(json))


if __name__ == '__main__':
    socketio.run(app, allow_unsafe_werkzeug=True)  # TODO: what does the allow_unsafe_werkzeug parameter do?
