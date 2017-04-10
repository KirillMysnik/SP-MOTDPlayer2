from commands.say import SayCommand
from core import console_message
from core.version import VERSION
from plugins.info import PluginInfo

from motdplayer import Page


info = PluginInfo(__name__)


def log_console(message):
    console_message("[{}] {}".format(info.verbose_name, message))


class Example1Page(Page):
    plugin_id = "motd_example1"
    page_id = "example1_page"

    def on_data_received(self, data):
        if data['action'] == "get-sp-version":
            self.send_data({'version': VERSION})

        else:
            log_console("Error! Unexpected action: {}".format(data['action']))


@SayCommand('!example1_page')
def say_test_st_page(command, index, team_only):
    Example1Page.send(index)
