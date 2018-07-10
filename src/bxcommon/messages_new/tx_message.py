from bxcommon.messages_new.blob_message import BlobMessage


class TxMessage(BlobMessage):
    def __init__(self, msg_hash=None, blob=None, buf=None):
        BlobMessage.__init__(self, 'tx', msg_hash, blob, buf)
