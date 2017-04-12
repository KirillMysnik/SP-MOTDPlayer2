from enum import IntEnum


class SessionError(IntEnum):
    TAKEN_OVER = 0
    PLAYER_DROP = 1
    UNKNOWN_PLAYER = 2
    WS_TRANSMISSION_END = 3
    WS_SWITCHED_FROM = 4
