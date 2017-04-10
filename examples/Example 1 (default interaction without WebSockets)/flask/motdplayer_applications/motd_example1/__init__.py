# =============================================================================
# >> IMPORTS
# =============================================================================
# Flask-MOTDPlayer
from motdplayer import WebRequestProcessor


# =============================================================================
# >> WEB REQUEST PROCESSORS
# =============================================================================
wrp_example1_page = WebRequestProcessor('motd_example1', 'example1_page')


# =============================================================================
# >> WEB REQUEST PROCESSOR CALLBACKS
# =============================================================================
# example1_page
@wrp_example1_page.register_regular_callback
def callback(ex_data_func):
    context = {
        'sp_version': ex_data_func(action="get-sp-version")['version'],
    }
    return "motd_example1/page.html", context
