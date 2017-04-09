from hashlib import sha512
import os.path
from random import choice
import string

from . import AuthMethod, MOTDPLAYER_DATA_PATH


SALT_CHARACTERS = string.ascii_letters + string.digits
SALT_LENGTH = 64
SERVER_SALTS_DIR = os.path.join(MOTDPLAYER_DATA_PATH, "server_salts")


server_salts = {}
for item in os.listdir(SERVER_SALTS_DIR):
    full_item = os.path.join(SERVER_SALTS_DIR, item)

    if os.path.isfile(full_item) and full_item.lower().endswith('.dat'):
        base_item = os.path.splitext(item)[0]
        with open(full_item, 'rb') as f:
            server_salts[base_item] = f.read()


User = None


def init(app, db):
    global User

    class User(db.Model):
        __tablename__ = "motdplayer_users"

        id = db.Column(db.Integer, primary_key=True)
        server_id = db.Column(db.String(32))
        steamid = db.Column(db.String(32))
        salt = db.Column(db.String(64))
        web_salt = db.Column(db.String(64))

        def __init__(self, server_id, steamid):
            super(User, self).__init__()

            self.server_id = server_id
            self.steamid = steamid
            self.salt = ""
            self.web_salt = ""

        def get_auth_token(self, plugin_id, page_id, session_id):
            return sha512(
                (
                    self.salt +
                    self.server_id +
                    plugin_id +
                    self.steamid +
                    page_id +
                    str(session_id)
                ).encode('ascii') + server_salts[self.server_id]
            ).hexdigest()

        def get_web_auth_token(self, plugin_id, page_id, session_id):
            return sha512(
                (
                    self.web_salt +
                    self.server_id +
                    plugin_id +
                    self.steamid +
                    page_id +
                    str(session_id)
                ).encode('ascii') + server_salts[self.server_id]
            ).hexdigest()

        def authenticate(
                self, method, plugin_id, page_id, auth_token, session_id):

            if method == AuthMethod.SRCDS:
                return auth_token == self.get_auth_token(
                    plugin_id, page_id, session_id)

            if method == AuthMethod.WEB:
                return auth_token == self.get_web_auth_token(
                    plugin_id, page_id, session_id)

            return False

        @staticmethod
        def get_new_salt():
            return ''.join(
                [choice(SALT_CHARACTERS) for x in range(SALT_LENGTH)])
