import sys

class DualStreamHandler:
    """
    Class that directs stderr and stdout both to the console as well as a popup to the client.
    """
    def __init__(self, socketio_instance):
        self.socketio_instance = socketio_instance
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
            self.socketio_instance.emit('console', {'data': message}, namespace='/crisscross') # this function sends the message to the client to show the error popup

    def flush(self):
        self._stdout.flush()
