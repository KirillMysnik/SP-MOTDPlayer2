from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from motdplayer.ws import Sockets


application = Flask(__name__)
sockets = None if Sockets is None else Sockets(application)

APP_SETTINGS = 'settings'
application.config.from_object(APP_SETTINGS)

db = SQLAlchemy(application)

import motdplayer
motdplayer.init(application, sockets, db)

import motdplayer_applications

db.create_all()
db.session.commit()

if __name__ == "__main__":
    application.run(debug=True)
