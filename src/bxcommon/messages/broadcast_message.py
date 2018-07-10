from bxcommon.messages.blob_message import BlobMessage


class BroadcastMessage(BlobMessage):
    def __init__(self, msg_hash=None, blob=None, buf=None):
        BlobMessage.__init__(self, 'broadcast', msg_hash, blob, buf)
