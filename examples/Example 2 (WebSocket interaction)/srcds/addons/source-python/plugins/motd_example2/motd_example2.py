from commands.say import SayCommand
from core import console_message
from events import Event
from messages import SayText2
from players.entity import Player
from plugins.info import PluginInfo

from motdplayer import Page


info = PluginInfo(__name__)
_ws_pages = []


def log_console(message):
    console_message("[{}] {}".format(info.verbose_name, message))


class Example2Page(Page):
    plugin_id = "motd_example2"
    page_id = "example2_page"
    ws_support = True

    def __init__(self, index, page_request_type):
        super().__init__(index, page_request_type)

        self.player_name = ""

        if self.is_websocket:
            self.player_name = Player(index).name
            _ws_pages.append(self)

    def on_data_received(self, data):
        if data['action'] == "chat-message":
            SayText2("{} through MOTD: '{}'".format(
                self.player_name, data['message'])).send()

        else:
            log_console("Error! Unexpected action: {}".format(data['action']))

    def on_error(self, error):
        if self.is_websocket and self in _ws_pages:
            _ws_pages.remove(self)


@SayCommand('!example2_page')
def say_test_ws_page(command, index, team_only):
    Example2Page.send(index)


@Event('player_death')
def on_player_death(ev):
    player_name = Player.from_userid(ev['userid']).name
    for ws_page in _ws_pages:
        ws_page.send_data({
            'action': "somebody-dead",
            'name': player_name
        })
