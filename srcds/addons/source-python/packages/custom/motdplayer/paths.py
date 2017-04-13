from paths import CFG_PATH, CUSTOM_DATA_PATH


MOTDPLAYER_DATA_PATH = CUSTOM_DATA_PATH / "motdplayer"
MOTDPLAYER_CFG_PATH = CFG_PATH / "motdplayer"


def get_server_file(path):
    server_path = path.dirname() / (path.namebase + "_server" + path.ext)
    if server_path.isfile():
        return server_path
    return path
