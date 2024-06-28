from flask import Flask, abort, render_template

from markupsafe import escape
from flask_socketio import SocketIO
from flask_socketio import send, emit

#For file uploads
from flask import request, redirect, url_for
from werkzeug.utils import secure_filename
import os

#For data handling
import numpy as np

app = Flask(__name__)


app.config['SECRET_KEY'] = 'secret!'

#For file uploading!
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Directory to save uploaded files
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}  # Allowed file extensions

# Ensure the upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


socketio = SocketIO(app)

#Functions for file upload:
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def slatDictToArray(gridDict):

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

    if(gridDict):
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
    if(array.shape != ()):
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


@socketio.on('upload_file')
def handle_upload_file(data):
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



@socketio.on('design saved')
def handle_my_custom_event(crisscrossDict):
    print('Design has been saved')
    slatArray = slatDictToArray(crisscrossDict[0])
    cargoArray = cargoDictToArray(crisscrossDict[1])

    # Save the arrays to a .npy file
    np.save('slatArray.npy', slatArray)
    np.save('cargoArray.npy', cargoArray)


@socketio.on('design import request')
def handle_my_custom_event():
    print('Design will be imported')
    slatArray = np.load('slatArray.npy', allow_pickle=True)
    #print(slatArray)
    cargoArray = np.load('cargoArray.npy', allow_pickle=True)
    slatDict = arrayToDict(slatArray)
    cargoDict = arrayToDict(cargoArray)
    emit('design import sent', [slatDict, cargoDict]);


#@socketio.on('my layer removed event')
#def handle_my_custom_event(json):
#    print('Layer removed: ' + str(json))


if __name__ == '__main__':
    socketio.run(app, allow_unsafe_werkzeug=True)


    
