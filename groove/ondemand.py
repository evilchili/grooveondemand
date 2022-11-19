from bottle import Bottle

server = Bottle()


@server.route('/')
def index():
    return "Groovy."
