from bxcommon.services.transaction_service import TransactionService
from bxcommon.utils.alarm import AlarmQueue


class MockNode(object):
    def __init__(self, server_ip, server_port, is_manager=False):
        self.server_ip = server_ip
        self.server_port = server_port
        self.alarm_queue = AlarmQueue()
        self.tx_service = TransactionService(self)
        self.is_manager = is_manager

        self.broadcast_messages = []

    def broadcast(self, msg, requester):
        self.broadcast_messages.append(msg)
