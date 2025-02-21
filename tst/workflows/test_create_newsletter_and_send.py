import datetime as dt

import pytest

from src.ai.client import WalterAI
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.s3.client import WalterS3Client
from src.aws.ses.client import WalterSESClient
from src.database.client import WalterDB
from src.database.stocks.models import Stock
from src.database.users.models import User
from src.database.userstocks.models import UserStock
from src.events.parser import WalterEventParser
from src.news.bucket import NewsSummariesBucket
from src.newsletters.client import NewslettersBucket
from src.newsletters.queue import NewslettersQueue
from src.stocks.client import WalterStocksAPI
from src.summaries.models import NewsSummary
from src.templates.bucket import TemplatesBucket
from src.templates.engine import TemplatesEngine
from src.workflows.create_newsletter_and_send import CreateNewsletterAndSend

#############
# CONSTANTS #
#############

BOB = User(
    email="bob@gmail.com",
    username="bob",
    password_hash="bob",
    verified=True,
    subscribed=True,
)
"""(User): The Walter user to create and send a portfolio newsletter."""

AAPL = Stock(
    symbol="AAPL",
    company="Apple Inc",
    description="Apple Inc. is an American multinational technology company that specializes in consumer electronics, computer software, and online services. Apple is the world's largest technology company by revenue (totalling $274.5 billion in 2020) and, since January 2021, the world's most valuable company. As of 2021, Apple is the world's fourth-largest PC vendor by unit sales, and fourth-largest smartphone manufacturer. It is one of the Big Five American information technology companies, along with Amazon, Google, Microsoft, and Facebook.",
    exchange="NASDAQ",
    industry="ELECTRONIC COMPUTERS",
    sector="TECHNOLOGY",
    official_site="https://www.apple.com",
    address="ONE INFINITE LOOP, CUPERTINO, CA, US",
)
"""(Stock): The model stock object for Apple. """

META = Stock(
    symbol="META",
    company="Meta Platforms Inc.",
    description="Meta Platforms, Inc. develops products that enable people to connect and share with friends and family through mobile devices, PCs, virtual reality headsets, wearables and home devices around the world. The company is headquartered in Menlo Park, California.",
    exchange="NASDAQ",
    industry="SERVICES-COMPUTER PROGRAMMING, DATA PROCESSING, ETC.",
    sector="TECHNOLOGY",
    official_site="https://investor.fb.com",
    address="1601 WILLOW ROAD, MENLO PARK, CA, US",
)
"""(Stock): The model stock object for Meta."""

BOBS_STOCKS = [
    UserStock(user_email=BOB.email, stock_symbol=AAPL.symbol, quantity=1.0),
    UserStock(user_email=BOB.email, stock_symbol=META.symbol, quantity=2.0),
]
"""(List[UserStock]): The stocks owned by the Walter user Bob."""

############
# FIXTURES #
############


# TODO: Mock this
@pytest.fixture
def walter_ai() -> WalterAI:
    pass


# TODO: Mock this
@pytest.fixture
def walter_ses() -> WalterSESClient:
    pass


@pytest.fixture
def create_newsletter_and_send_workflow(
    walter_authenticator: WalterAuthenticator,
    walter_event_parser: WalterEventParser,
    walter_db: WalterDB,
    walter_stocks_api: WalterStocksAPI,
    walter_ai: WalterAI,
    walter_ses: WalterSESClient,
    walter_cw: WalterCloudWatchClient,
    template_engine: TemplatesEngine,
    templates_bucket: TemplatesBucket,
    news_summaries_bucket: NewsSummariesBucket,
    newsletters_bucket: NewslettersBucket,
    newsletters_queue: NewslettersQueue,
) -> CreateNewsletterAndSend:
    return CreateNewsletterAndSend(
        walter_authenticator,
        walter_event_parser,
        walter_db,
        walter_stocks_api,
        walter_ai,
        walter_ses,
        walter_cw,
        template_engine,
        templates_bucket,
        news_summaries_bucket,
        newsletters_bucket,
        newsletters_queue,
    )


def test_create_newsletter_and_send_get_user_success(
    create_newsletter_and_send_workflow: CreateNewsletterAndSend,
) -> None:
    user = create_newsletter_and_send_workflow._get_user(email=BOB.email)
    assert user == BOB


def test_create_newsletter_and_send_get_portfolio_success(
    create_newsletter_and_send_workflow: CreateNewsletterAndSend,
) -> None:
    portfolio = create_newsletter_and_send_workflow._get_portfolio(BOB)
    assert set(portfolio.get_stocks()) == set(BOBS_STOCKS)
    assert portfolio.get_equity(AAPL.symbol) == 100.0
    assert portfolio.get_equity(META.symbol) == 500.0
    assert portfolio.get_total_equity() == 600.0


def test_create_newsletter_and_send_get_latest_news_summaries_success(
    create_newsletter_and_send_workflow: CreateNewsletterAndSend,
) -> None:
    date = dt.datetime(
        year=2025, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
    )
    summaries = create_newsletter_and_send_workflow._get_latest_news_summaries(
        [AAPL.symbol, META.symbol]
    )
    assert set(summaries) == {
        NewsSummary(
            stock=AAPL.symbol,
            company=AAPL.company,
            datestamp=date,
            model_name="Amazon: Nova Lite",
            news=None,
            summary="Test Apple Summary",
        ),
        NewsSummary(
            stock=META.symbol,
            company=META.company,
            datestamp=date,
            model_name="Amazon: Nova Lite",
            news=None,
            summary="Test Meta Summary",
        ),
    }


def test_create_newsletter_and_send_get_template_spec_success(
    create_newsletter_and_send_workflow: CreateNewsletterAndSend,
) -> None:
    user = create_newsletter_and_send_workflow._get_user(email=BOB.email)
    portfolio = create_newsletter_and_send_workflow._get_portfolio(user=BOB)
    summaries = create_newsletter_and_send_workflow._get_latest_news_summaries(
        [AAPL.symbol, META.symbol]
    )
    template_spec = create_newsletter_and_send_workflow._get_template_spec(
        user, portfolio, summaries
    )
    assert template_spec.context.user == BOB.username
    assert template_spec.context.portfolio_value == "$600.00"
    assert template_spec.context.stocks == [
        {"Symbol": AAPL.symbol, "Shares": 1.0, "Price": 100.0, "Equity": 100.0},
        {"Symbol": META.symbol, "Shares": 2.0, "Price": 250.0, "Equity": 500.0},
    ]


def test_create_newsletter_and_send_get_unsubscribe_link_success(
    create_newsletter_and_send_workflow: CreateNewsletterAndSend, jwt_bob: str
) -> None:
    unsubscribe_link = create_newsletter_and_send_workflow._get_unsubscribe_link(
        BOB.email
    )
    assert unsubscribe_link == f"https://walterai.dev/unsubscribe?token={jwt_bob}"


def test_create_newsletter_and_send_archive_newsletter_success(
    create_newsletter_and_send_workflow: CreateNewsletterAndSend,
    walter_s3: WalterS3Client,
) -> None:
    datestamp = dt.datetime.now().strftime("y=%Y/m=%m/d=%d")
    assert (
        walter_s3.get_object(
            "walterai-newsletters-unittest",
            f"newsletters/{datestamp}/bob/default/index.html",
        )
        is None
    )
    create_newsletter_and_send_workflow._archive_newsletter(BOB, "", "default")
    assert (
        walter_s3.get_object(
            "walterai-newsletters-unittest",
            f"newsletters/{datestamp}/bob/default/index.html",
        )
        is not None
    )
