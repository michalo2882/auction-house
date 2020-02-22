class FailedToCreateListingError(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg


class FailedToMakeTransactionError(Exception):
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg


class CannotAffordError(Exception):
    ...


class InvalidTransactionError(Exception):
    ...
