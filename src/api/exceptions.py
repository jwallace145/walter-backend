class InvalidEmail(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidPassword(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidUsername(Exception):
    def __init__(self, message):
        super().__init__(message)


class UserAlreadyExists(Exception):
    def __init__(self, message):
        super().__init__(message)


class UserDoesNotExist(Exception):
    def __init__(self, message):
        super().__init__(message)


class StockDoesNotExist(Exception):
    def __init__(self, message):
        super().__init__(message)


class BadRequest(Exception):
    def __init__(self, message):
        super().__init__(message)


class NotAuthenticated(Exception):
    def __init__(self, message):
        super().__init__(message)


class EmailNotVerified(Exception):
    def __init__(self, message):
        super().__init__(message)
