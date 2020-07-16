class NonVersionMessageError(Exception):
    def __init__(self, msg: str, is_known: bool) -> None:
        super().__init__(msg)
        self.msg: str = msg
        self.is_known: bool = is_known
