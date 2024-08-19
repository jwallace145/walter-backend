from dataclasses import dataclass


@dataclass
class Stock:
    symbol: str
    company: str

    def to_ddb_item(self) -> dict:
        return {
            "symbol": {
                "S": self.symbol,
            },
            "company": {"S": self.company},
        }
