from configparser import ConfigParser
from datetime import datetime
from enum import IntEnum
import json
import os.path


MOTDPLAYER_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
CONFIG_INI_PATH = os.path.join(MOTDPLAYER_DATA_PATH, "config.ini")
SERVERS_JSON_PATH = os.path.join(MOTDPLAYER_DATA_PATH, "servers.json")


class AuthMethod(IntEnum):
    SRCDS = 0
    WEB = 1


config = ConfigParser()
config.read(CONFIG_INI_PATH)

with open(SERVERS_JSON_PATH, 'r') as f:
    servers = json.load(f)

sockets = None
db = None
User = None


def init(app, sockets_, db_):
    global sockets, db, User
    sockets = sockets_
    db = db_

    from . import database
    database.init(app, db)
    User = database.User

    from . import views
    views.init(app, db)

    @app.after_request
    def disable_caching(response):
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = (
            "no-store, no-cache, must-revalidate, post-check=0, "
            "pre-check=0, max-age=0")
        response.headers['Pragma'] = "no-cache"
        response.headers['Expires'] = "-1"
        return response


wrps = {}


class WebRequestProcessor:
    def __init__(self, plugin_id, page_id):
        self.regular_callback = None
        self.ajax_callback = None
        self.ws_callback = None

        if plugin_id not in wrps:
            wrps[plugin_id] = {}

        if page_id in wrps[plugin_id]:
            raise ValueError(
                "WebRequestProcessor with page_id='{}' is already registered "
                "for plugin '{}'".format(page_id, plugin_id))

        wrps[plugin_id][page_id] = self

    def register_regular_callback(self, callback):
        self.regular_callback = callback
        return callback

    def register_ajax_callback(self, callback):
        self.ajax_callback = callback
        return callback

    def register_ws_callback(self, callback):
        self.ws_callback = callback
        return callback
