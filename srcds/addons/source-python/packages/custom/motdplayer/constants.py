from enum import IntEnum


class SessionError(IntEnum):
    TAKEN_OVER = 0
    PLAYER_DROP = 1
    WS_TRANSMISSION_END = 2
    WS_SWITCHED_FROM = 3


class PageRequestType(IntEnum):
    INIT = 0
    AJAX = 1
    WEBSOCKET = 2
