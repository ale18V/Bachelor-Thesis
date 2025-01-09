class NotBroadcastableMessage(Exception):
    pass


class DuplicateMessage(NotBroadcastableMessage):
    pass


class InvalidMessage(NotBroadcastableMessage):
    pass
