from dataclasses import dataclass
import datetime as dt
from src.aws.s3.client import WalterS3Client
from src.environment import Domain
from src.stocks.alphavantage.models import CompanyNews
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterKnowledgeBase:
    """
    WalterKnowledgeBase

    Bucket: walter-knowledge-base-{domain}
    """

    BUCKET = "walter-knowledge-base-{domain}"
    KEY = "{symbol}/year={year}/{filename}"

    s3: WalterS3Client

    bucket: str = None  # set during init

    def __post_init__(self) -> None:
        self.bucket = WalterKnowledgeBase._get_bucket_name(self.s3.domain)
        log.debug(f"Creating WalterKnowledgeBase client with bucket '{self.bucket}'")

    def add_news(self, news: CompanyNews) -> None:
        log.info(f"Adding news for company '{news.symbol}' to knowledge base")
        stock = news.symbol
        for title, contents in news.news.items():
            self._dump_article(stock, title, contents)
        log.info(
            "Successfully dumped news for company '{news.symbol}' to knowledge base!"
        )

    def _dump_article(self, symbol: str, title: str, contents: str) -> None:
        key = WalterKnowledgeBase._get_key(symbol, title)
        self.s3.put_object(self.bucket, key=key, contents=contents)

    @staticmethod
    def _get_bucket_name(domain: Domain) -> str:
        return WalterKnowledgeBase.BUCKET.format(domain=domain.value)

    @staticmethod
    def _get_key(symbol: str, title: str) -> str:
        return WalterKnowledgeBase.KEY.format(
            symbol=symbol.upper(), year=dt.datetime.now(dt.UTC).year, filename=title
        )
