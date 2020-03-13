class NonVersionMessageError(Exception):
    def __init__(self, msg: str, is_known: bool):
        self.msg: str = msg
        self.is_known: bool = is_known
