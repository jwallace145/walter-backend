from src.environment import Domain


#############
# CONSTANTS #
#############

AWS_REGION = "us-east-1"
"""(str): The unit test AWS region."""

################
# TEST SECRETS #
################

SECRETS_MANAGER_ALPHA_VANTAGE_API_KEY_NAME = "AlphaVantageAPIKey"
SECRETS_MANAGER_ALPHA_VANTAGE_API_KEY_VALUE = "test-alpha-vantage-api-key"

SECRETS_MANAGER_POLYGON_API_KEY_NAME = "PolygonAPIKey"
SECRETS_MANAGER_POLYGON_API_KEY_VALUE = "test-polygon-api-key"

SECRETS_MANAGER_JWT_SECRET_KEY_SECRET_NAME = "JWTSecretKey"
SECRETS_MANAGER_JWT_SECRET_KEY_SECRET_VALUE = "test-jwt-secret-key"

SECRETS_MANAGER_CHANGE_PASSWORD_KEY_SECRET_NAME = "JWTChangePasswordSecretKey"
SECRETS_MANAGER_CHANGE_PASSWORD_KEY_SECRET_VALUE = "test-change-password-key"

SECRETS_MANAGER_VERIFY_EMAIL_KEY_SECRET_NAME = "JWTVerifyEmailSecretAccessKey"
SECRETS_MANAGER_VERIFY_EMAIL_KEY_SECRET_VALUE = "test-verify-email-key"

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
