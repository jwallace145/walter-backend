class UnknownModel(Exception):
    """
    UnknownModel

    The exception raised when an unknown/unsupported model is
    given to WalterAI.
    """

    def __init__(self, message):
        super().__init__(message)
