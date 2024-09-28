from flask import Flask
from flask_socketio import SocketIO

import sys
import os

from GUI.backend_functions.debugging_error_preview import DualStreamHandler
from crisscross.helper_functions import create_dir_if_empty
from crisscross.helper_functions.plate_constants import base_directory


if __name__ == '__main__':
    app = Flask(__name__,
                template_folder=os.path.join(base_directory, 'GUI', 'base_html'),
                static_folder=os.path.join(base_directory, 'GUI', 'static'))

    app.config['UPLOAD_FOLDER'] = os.path.join(base_directory, 'GUI', 'temp_files', 'uploads')  # Directory to save uploaded files
    app.config['OUTPUT_FOLDER'] = os.path.join(base_directory, 'GUI', 'temp_files',  'design_outputs')
    app.config['PLATE_FOLDER'] = os.path.join(base_directory, 'GUI', 'temp_files',  'plates') # Directory to save uploaded files
    app.config['ZIP_FOLDER'] = os.path.join(base_directory, 'GUI', 'temp_files',  'zip_outputs') # Directory to save uploaded files

    app.config['ALLOWED_EXTENSIONS'] = {'txt', 'npz', 'xlsx'}  # Allowed file extensions
    app.config['PLATE_ALLOWED_EXTENSIONS'] = {'xlsx'}  # Allowed file extensions

    socketio_instance = SocketIO(app, max_http_buffer_size=100 * 1024 * 1024)  # Set max transfer size 100MB

    # Ensure the upload directory exists
    create_dir_if_empty(app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER'], app.config['PLATE_FOLDER'])

    with app.app_context():
        from GUI.backend_functions.routing_and_sockets import SocketNamespace

        namespace = SocketNamespace('/crisscross')
        socketio_instance.on_namespace(namespace)

        # Replace sys.stdout and sys.stderr with the dual handler
        sys.stdout = DualStreamHandler(socketio_instance)
        sys.stderr = DualStreamHandler(socketio_instance)

        socketio_instance.run(app, allow_unsafe_werkzeug=True)  # TODO: apparently the werkzeug server helps for debugging, but is not good for production.  Will need to investigate eventlet or gevent for production....


