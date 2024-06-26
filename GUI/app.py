from flask import Flask, abort, render_template
from markupsafe import escape
from flask_socketio import SocketIO

app = Flask(__name__)


app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('my event')
def handle_my_custom_event(json):
    print('received json: ' + str(json))

@socketio.on('slat placed')
def handle_my_custom_event(json):
    print('A slat has been placed, and grid generated: ')
    print(json)

@socketio.on('my layer removed event')
def handle_my_custom_event(json):
    print('Layer removed: ' + str(json))


if __name__ == '__main__':
    socketio.run(app)


    

#app = Flask(__name__)
#
#@app.route('/')
#def index():
#    return render_template('index.html')
#
#@app.route('/about/')
#def about():
#    return '<h3> This is a Flask web application.<h3>'
#
#@app.route('/capitalize/<word>/')
#def capitalize(word):
#    return '<h1>{}</h1>'.format(escape(word.capitalize()))
#
#@app.route('/add/<int:n1>/<int:n2>/')
#def add(n1, n2):
#    return '<h1>{}</h1>'.format(n1 + n2)
#
#@app.route('/users/<int:user_id>')
#def greet_user(user_id):
#    users = ['Bob', 'Jane', 'Adam']
#    try:
#        return '<h2>Hi {}</h2>'.format(users[user_id])
#    except IndexError:
#        abort(404)