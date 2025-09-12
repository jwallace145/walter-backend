class InvalidEmail(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidPassword(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidName(Exception):
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


class SessionDoesNotExist(Exception):
    def __init__(self, message):
        super().__init__(message)


class SessionExpired(Exception):
    def __init__(self, message):
        super().__init__(message)


class SessionRevoked(Exception):
    def __init__(self, message):
        super().__init__(message)


class EmailNotVerified(Exception):
    def __init__(self, message):
        super().__init__(message)


class EmailAlreadyVerified(Exception):
    def __init__(self, message):
        super().__init__(message)


class EmailNotSubscribed(Exception):
    def __init__(self, message):
        super().__init__(message)


class EmailAlreadySubscribed(Exception):
    def __init__(self, message):
        super().__init__(message)


class EmailAlreadyUnsubscribed(Exception):
    def __init__(self, message):
        super().__init__(message)


class MaximumNumberOfStocks(Exception):
    def __init__(self, message):
        super().__init__(message)


class UnknownPaymentStatus(Exception):
    def __init__(self, message):
        super().__init__(message)


class NewsletterDoesNotExist(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidExpenseCategory(Exception):
    def __init__(self, message):
        super().__init__(message)


class TransactionDoesNotExist(Exception):
    def __init__(self, message):
        super().__init__(message)


class PlaidAccessTokenDoesNotExist(Exception):
    def __init__(self, message):
        super().__init__(message)


class PlaidItemDoesNotExist(Exception):
    def __init__(self, message):
        super().__init__(message)


class PlaidItemAlreadyExists(Exception):
    def __init__(self, message):
        super().__init__(message)


class InvalidPlaidInstitution(Exception):
    def __init__(self, message):
        super().__init__(message)


class AccountDoesNotExist(Exception):
    def __init__(self, message):
        super().__init__(message)


class SecurityDoesNotExist(Exception):
    def __init__(self, message):
        super().__init__(message)


class HoldingDoesNotExist(Exception):
    def __init__(self, message):
        super().__init__(message)
