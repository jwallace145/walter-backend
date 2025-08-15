from dataclasses import dataclass


@dataclass
class MarketExchange:
    name: str
    key_name: str


# Market exchange code to MarketExchange mapping - only popular exchanges
MARKET_EXCHANGES = {
    # Major US Stock Exchanges
    "XNAS": MarketExchange(name="NASDAQ Global Select Market", key_name="nasdaq"),
    "XNYS": MarketExchange(name="New York Stock Exchange", key_name="nyse"),
    "ARCX": MarketExchange(name="NYSE Arca", key_name="nyse_arca"),
    "BATS": MarketExchange(name="Cboe BZX Exchange", key_name="cboe_bzx"),
    "XASE": MarketExchange(name="NYSE American", key_name="nyse_american"),
    "IEXG": MarketExchange(name="Investors Exchange", key_name="iex"),
    # Over-the-Counter Markets
    "OTCM": MarketExchange(name="OTC Markets", key_name="otc_markets"),
    "OTCP": MarketExchange(name="OTC Pink Sheets", key_name="otc_pink"),
    "OTCQ": MarketExchange(name="OTCQX Best Market", key_name="otcqx"),
    "OTCX": MarketExchange(name="OTCQB Venture Market", key_name="otcqb"),
    # International Exchanges
    "XTSE": MarketExchange(name="Toronto Stock Exchange", key_name="tsx"),
    "XLON": MarketExchange(name="London Stock Exchange", key_name="lse"),
    "XPAR": MarketExchange(name="Euronext Paris", key_name="euronext_paris"),
    "XFRA": MarketExchange(name="Deutsche Börse Frankfurt", key_name="frankfurt"),
    "XSWX": MarketExchange(name="SIX Swiss Exchange", key_name="swiss"),
    "XSTO": MarketExchange(name="Nasdaq Stockholm", key_name="nasdaq_stockholm"),
    "XHKG": MarketExchange(name="Hong Kong Stock Exchange", key_name="hkex"),
    "XSHG": MarketExchange(name="Shanghai Stock Exchange", key_name="sse"),
    "XTKS": MarketExchange(name="Tokyo Stock Exchange", key_name="tse"),
    "XASX": MarketExchange(name="Australian Securities Exchange", key_name="asx"),
    # Crypto Exchanges
    "COIN": MarketExchange(name="Coinbase", key_name="coinbase"),
    "BINA": MarketExchange(name="Binance", key_name="binance"),
    "KRKN": MarketExchange(name="Kraken", key_name="kraken"),
    "BITF": MarketExchange(name="Bitfinex", key_name="bitfinex"),
    "BSTM": MarketExchange(name="Bitstamp", key_name="bitstamp"),
    "GEMS": MarketExchange(name="Gemini", key_name="gemini"),
    # Default/Unknown
    "UNK": MarketExchange(name="Unknown Exchange", key_name="unknown"),
    "": MarketExchange(name="Not Specified", key_name="not_specified"),
}


def get_market_exchange(exchange_code: str) -> MarketExchange:
    return MARKET_EXCHANGES.get(exchange_code.upper(), MARKET_EXCHANGES["UNK"])
