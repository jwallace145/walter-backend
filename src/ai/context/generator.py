from dataclasses import dataclass
from typing import Dict

from src.ai.context.models import Context
from src.database.users.models import User
from src.stocks.models import Portfolio
from src.stocks.polygon.models import StockPrice
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class ContextGenerator:

    stocks: Dict[str, StockPrice] = None

    def __post_init__(self) -> None:
        log.debug("Creating ContextGenerator")

    def get_context(self, user: User, portfolio: Portfolio) -> Context:
        log.info(f"Creating context for {user}")

        context = f"Generate an investments newsletter for {user.username} in a business casual fashion with jokes.\n"
        context += f"{user.username} total portfolio value is ${portfolio.get_total_equity():.2f}"
        context += "Use the following financial data for writing the newsletter.\n"

        for stock in portfolio.get_stock_symbols():
            news = portfolio.get_news(stock)
            context += "\n".join(news.descriptions)

        return Context(context)
