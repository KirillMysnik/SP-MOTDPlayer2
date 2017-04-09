# =============================================================================
# >> IMPORTS
# =============================================================================
# Flask-MOTDPlayer
from motdplayer import WebRequestProcessor


# =============================================================================
# >> WEB REQUEST PROCESSORS
# =============================================================================
wrp_test_st_page = WebRequestProcessor('test_motd_plugin', 'test_static_page')
wrp_test_ws_page = WebRequestProcessor(
    'test_motd_plugin', 'test_websocket_page')


# =============================================================================
# >> WEB REQUEST PROCESSOR CALLBACKS
# =============================================================================
# test_st_page
@wrp_test_st_page.register_regular_callback
def callback(ex_data_func):
    context = {
        'sp_version': ex_data_func(action="get-version")['version'],
    }
    return "test_application/test_st_page.html", context


# test_ws_page
@wrp_test_ws_page.register_regular_callback
def callback(ex_data_func):
    return "test_application/test_ws_page.html", {}


@wrp_test_ws_page.register_ws_callback
def callback(data):
    return data
