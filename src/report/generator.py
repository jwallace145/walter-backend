from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List

from src.dynamodb.models import Stock, User
from src.polygon.models import StockPrice
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class ReportGenerator:

    stocks: Dict[str, StockPrice] = None

    def __post_init__(self) -> None:
        log.debug("Creating ReportGenerator")
        self.stocks = defaultdict(lambda: [])

    def get_profits(self, stocks: List[Stock]) -> str:
        prompt = ""

        for stock, prices in self._extract_stocks_for_user(stocks).items():
            sorted_prices = sorted(prices)
            gain = sorted_prices[-1].price - sorted_prices[0].price

            if gain > 0:
                prompt += f" {stock} made ${gain:.2f} in profit!"

        if prompt == "":
            prompt += "User made no profits on any stocks."

        return prompt

    def get_losses(self, stocks: List[Stock]) -> None:
        prompt = ""

        for stock, prices in self._extract_stocks_for_user(stocks).items():
            sorted_prices = sorted(prices)
            gain = sorted_prices[-1].price - sorted_prices[0].price

            if gain < 0:
                prompt += f" {stock} lost ${-1*gain:.2f}!"

        if prompt == "":
            prompt += "User did not lose any money on any stocks"

        return prompt

    def generate_report(self, user: User, stocks: List[Stock]) -> None:
        log.info(f"Generating report for user {user} and {len(stocks)} stocks")

        report = f"Generate an investments newsletter for {user.username} in a business casual fashion with jokes.\n"
        report += "Use the following financial data for writing the newsletter.\n"

        total_gain = 0
        for stock, prices in self._extract_stocks_for_user(stocks).items():
            sorted_prices = sorted(prices)
            gain = sorted_prices[-1].price - sorted_prices[0].price
            if gain > 0:
                report += f"{user.username} made ${gain:.2f} on stock {stock}.\n"
            elif gain < 0:
                report += f"{user.username} lost -${-1*gain:.2f} on stock {stock}.\n"
            else:
                report += f"{user.username} made no money on stock {stock}.\n"
            total_gain += gain
        report += f"{user.username} made a total profit of ${total_gain:.2f}!"

        return report

    def ingest_stocks(self, stock_prices: List[StockPrice]) -> None:
        log.info("Ingesting stock data")
        for stock in stock_prices:
            self.stocks[stock.symbol].append(stock)

    def _extract_stocks_for_user(self, stocks: List[Stock]) -> Dict[str, StockPrice]:
        symbols = [stock.symbol for stock in stocks]
        return dict((symbol, self.stocks[symbol]) for symbol in symbols)
