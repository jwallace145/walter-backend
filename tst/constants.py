from src.environment import Domain


#############
# CONSTANTS #
#############

AWS_REGION = "us-east-1"
"""(str): The unit test AWS region."""

################
# TEST SECRETS #
################

SECRETS_TEST_FILE = "tst/aws/data/secrets.jsonl"
"""(str): The name of the test secrets input file."""

###################
# TEST DDB TABLES #
###################

STOCKS_TABLE_NAME = f"Stocks-{Domain.TESTING.value}"
"""(str): The name of the Stocks table that stores all the individual stocks."""

STOCKS_TEST_FILE = "tst/database/data/stocks.jsonl"
"""(str): The name of the test stocks input file."""

USERS_TABLE_NAME = f"Users-{Domain.TESTING.value}"
"""(str): The name of the Users table that stores all Walter users."""

USERS_TEST_FILE = "tst/database/data/users.jsonl"
"""(str): The name of the test users input file."""

USERS_STOCKS_TABLE_NAME = f"UsersStocks-{Domain.TESTING.value}"
"""(str): The name of the UsersStocks table that stores all stocks owned by users."""

USERS_STOCKS_TEST_FILE = "tst/database/data/usersstocks.jsonl"
"""(str): The name of the test user stocks input file."""

ACCOUNTS_TABLE_NAME = f"Accounts-{Domain.TESTING.value}"
"""(str): The name of the Accounts table that stores all accounts owned by users."""

ACCOUNTS_TEST_FILE = "tst/database/data/accounts.jsonl"
"""(str): The name of the test accounts input file."""

# Backward-compat constants (used by some mocks; not all are utilized in tests)
TRANSACTIONS_TABLE_NAME = f"Transactions-{Domain.TESTING.value}"
CASH_ACCOUNTS_TABLE_NAME = f"CashAccounts-{Domain.TESTING.value}"
CASH_ACCOUNTS_TEST_FILE = "tst/database/data/cash_accounts.jsonl"
CREDIT_ACCOUNTS_TABLE_NAME = f"CreditAccounts-{Domain.TESTING.value}"
CREDIT_ACCOUNTS_TEST_FILE = "tst/database/data/credit_accounts.jsonl"
INVESTMENT_ACCOUNTS_TABLE_NAME = f"InvestmentAccounts-{Domain.TESTING.value}"
INVESTMENT_ACCOUNTS_TEST_FILE = "tst/database/data/investment_accounts.jsonl"

###################
# TEST SQS QUEUES #
###################

NEWSLETTERS_QUEUE_NAME = f"NewslettersQueue-{Domain.TESTING.value}"
"""(str): The name of the Newsletter queue that queues CreateAndSendNewsletter events."""

NEWS_SUMMARIES_QUEUE_NAME = f"NewsSummariesQueue-{Domain.TESTING.value}"
"""(str): The name of the NewsSummaries queue that queues CreateAndArchiveSummary events."""


####################
# TEST STOCKS DATA #
####################

PRICES_TEST_FILE = "tst/stocks/data/prices.jsonl"
"""(str): The test prices input file to be returned by the mock Polygon client."""

NEWS_TEST_FILE = "tst/stocks/data/news.jsonl"
"""(str): The test news input file to be returned by the mock AlphaVantage client."""

COMPANIES_TEST_FILE = "tst/stocks/data/companies.jsonl"
"""(str): The test companies input file to be returned by the mock AlphaVantage client."""

################
# TEST S3 DATA #
################

OBJECTS_TEST_FILE = "tst/aws/data/objects.json"
"""(str): The test objects input file that contains the test S3 objects for unit tests."""

TEMPLATES_BUCKET_NAME = f"walterai-templates-{Domain.TESTING.value}"
"""(str): The name of the templates bucket for unit tests."""

NEWSLETTERS_BUCKET_NAME = f"walterai-newsletters-{Domain.TESTING.value}"
"""(str): The name of the newsletters bucket for unit tests."""

SUMMARIES_BUCKET_NAME = f"walterai-news-summaries-{Domain.TESTING.value}"
"""(str): The name of the summaries bucket for unit tests."""
