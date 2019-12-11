class MessageValidationError(Exception):
    def __init__(self, msg: str):
        super(MessageValidationError, self).__init__(msg)

        self.msg: str = msg
