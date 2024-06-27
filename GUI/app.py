from flask import Flask, abort, render_template

from markupsafe import escape
from flask_socketio import SocketIO
from flask_socketio import send, emit
import numpy as np

app = Flask(__name__)


app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


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


@socketio.on('my event')
def handle_my_custom_event(json):
    print('received json: ' + str(json))

@socketio.on('slat placed')
def handle_my_custom_event(crisscrossDict):
    print('A slat has been placed, and grid generated: ')
    slatArray = slatDictToArray(crisscrossDict[0])
    slatDict = arrayToDict(slatArray)

    emit('slat dict made', slatDict);


    print(type(slatArray))
    print(slatArray)

@socketio.on('cargo placed')
def handle_my_custom_event(gridArray):
    print('A cargo has been placed, and grid generated: ')
    print(type(gridArray))
    print(gridArray)

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
    print(slatArray)
    cargoArray = np.load('cargoArray.npy', allow_pickle=True)
    slatDict = arrayToDict(slatArray)
    cargoDict = arrayToDict(cargoArray)
    emit('design import sent', [slatDict, cargoDict]);


@socketio.on('my layer removed event')
def handle_my_custom_event(json):
    print('Layer removed: ' + str(json))


if __name__ == '__main__':
    socketio.run(app, allow_unsafe_werkzeug=True)


    
