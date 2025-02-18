class CompanyNewsNotFound(Exception):
    """
    This exception is raised when AlphaVantage finds no stock news
    for a given stock over a timeframe.

    Callers of the get_news() method should catch this exception
    to ensure they handle the edge-case where no stock news are
    found for the stock appropriately.
    """

    def __init__(self, message):
        super().__init__(message)
