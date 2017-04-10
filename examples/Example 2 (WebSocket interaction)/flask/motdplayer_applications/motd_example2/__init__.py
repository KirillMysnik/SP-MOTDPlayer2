# =============================================================================
# >> IMPORTS
# =============================================================================
# Flask-MOTDPlayer
from motdplayer import WebRequestProcessor


# =============================================================================
# >> WEB REQUEST PROCESSORS
# =============================================================================
wrp_example2_page = WebRequestProcessor('motd_example2', 'example2_page')


# =============================================================================
# >> WEB REQUEST PROCESSOR CALLBACKS
# =============================================================================
# example2_page
@wrp_example2_page.register_regular_callback
def callback(ex_data_func):
    return "motd_example2/page.html", dict()


@wrp_example2_page.register_ws_callback
def callback(data):
    return data
