from enum import Enum


class Platform(str, Enum):
    TELEGRAM = "telegram"


class InteractionType(str, Enum):
    TEXT = "text"
    BUTTON = "button"
    COMMAND = "command"
    VOICE = "voice"
    IMAGE = "image"
    DOCUMENT = "document"