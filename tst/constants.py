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

USERS_TABLE_NAME = f"Users-{Domain.TESTING.value}"
"""(str): The name of the Users table that stores all Walter users."""

USERS_TEST_FILE = "tst/database/data/users.jsonl"
"""(str): The name of the test users input file."""

ACCOUNTS_TABLE_NAME = f"Accounts-{Domain.TESTING.value}"
"""(str): The name of the Accounts table that stores all accounts owned by users."""

ACCOUNTS_TEST_FILE = "tst/database/data/accounts.jsonl"
"""(str): The name of the test accounts input file."""

SECURITIES_TABLE_NAME = f"Securities-{Domain.TESTING.value}"
"""(str): The name of the Securities table that stores all securities owned by users."""

SECURITIES_TEST_FILE = "tst/database/data/securities.jsonl"
"""(str): The name of the test securities input file."""

HOLDINGS_TABLE_NAME = f"Holdings-{Domain.TESTING.value}"
"""(str): The name of the Holdings table that stores all holdings of users."""

HOLDINGS_TEST_FILE = "tst/database/data/holdings.jsonl"
"""(str): The name of the test holdings input file."""

TRANSACTIONS_TABLE_NAME = f"Transactions-{Domain.TESTING.value}"
"""(str): The name of the Transactions table that stores all transactions made by users."""

TRANSACTIONS_TEST_FILE = "tst/database/data/transactions.jsonl"
"""(str): The name of the test transactions input file."""

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
