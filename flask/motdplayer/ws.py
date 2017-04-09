"""Based on https://gist.github.com/blaenk/8572079"""
from werkzeug.exceptions import NotFound
from werkzeug.routing import Map, Rule

try:
    import uwsgi
except ImportError:
    uwsgi = None
    print("MOTDPlayer: WebSocket support will be disabled "
          "because 'uwsgi' module is unavailable")


class SocketMiddleware:
    def __init__(self, wsgi_app, sockets):
        self.ws = sockets
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO']
        try:
            url, args = self.ws.url_map.bind_to_environ(environ).match(path)
            handler = self.ws.handlers[url]

            uwsgi.websocket_handshake()

            try:
                handler(**args)
            finally:
                return  # TODO: Return at least something

        except (NotFound, KeyError):
            return self.wsgi_app(environ, start_response)


class Sockets:
    def __init__(self, app=None):
        self.url_map = Map()
        self.handlers = dict()
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.wsgi_app = SocketMiddleware(app.wsgi_app, self)

    def route(self, rule, **options):
        def decorator(f):
            self.url_map.add(Rule(rule, endpoint=f.__name__))
            self.handlers[f.__name__] = f
            return f

        return decorator


if uwsgi is None:
    Sockets = None
