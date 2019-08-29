from enum import Flag


class NodeType(Flag):
    GATEWAY = 1
    RELAY_TRANSACTION = 2
    RELAY_BLOCK = 4
    INTERNAL = 8
    RELAY = RELAY_TRANSACTION | RELAY_BLOCK
    GATEWAY_INTERNAL = GATEWAY | INTERNAL

    def __str__(self):
        return self.name
