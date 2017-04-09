from commands.say import SayCommand
from core import console_message
from core.version import VERSION
from events import Event
from messages import SayText2
from players.entity import Player
from plugins.info import PluginInfo

from motdplayer import Page


PLUGIN_NAME = "test_motd_plugin"


info = PluginInfo(__name__)
_ws_pages = []


def log_console(message):
    console_message("[{}] {}".format(info.verbose_name, message))


class TestStaticPage(Page):
    plugin_id = PLUGIN_NAME
    page_id = "test_static_page"

    def on_data_received(self, data):
        if data['action'] == "get-version":
            self.send_data({'version': VERSION})

        else:
            log_console("Error! Unexpected action: {}".format(data['action']))


class TestWSPage(Page):
    plugin_id = PLUGIN_NAME
    page_id = "test_websocket_page"
    ws_support = True

    def __init__(self, index, ws_instance):
        super().__init__(index, ws_instance)

        self.player = None

        if ws_instance:
            self.player = Player(index)
            _ws_pages.append(self)

    def on_data_received(self, data):
        if data['action'] == "chat-message":
            SayText2("{} through MOTD: '{}'".format(
                self.player.name, data['message'])).send()

        else:
            log_console("Error! Unexpected action: {}".format(data['action']))

    def on_error(self, error):
        if self.ws_instance and self in _ws_pages:
            _ws_pages.remove(self)


@SayCommand('!test_st_page')
def say_test_st_page(command, index, team_only):
    TestStaticPage.send(index)


@SayCommand('!test_ws_page')
def say_test_ws_page(command, index, team_only):
    TestWSPage.send(index)


@Event('player_death')
def on_player_death(ev):
    player_name = Player.from_userid(ev['userid']).name
    for ws_page in _ws_pages:
        ws_page.send_data({
            'action': "somebody-dead",
            'name': player_name
        })
