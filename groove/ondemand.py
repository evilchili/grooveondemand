from bottle import Bottle, auth_basic
from groove.auth import is_authenticated

server = Bottle()


@server.route('/')
def index():
    return "Groovy."


@server.route('/admin')
@auth_basic(is_authenticated)
def admin():
    return "Authenticated. Groovy."
