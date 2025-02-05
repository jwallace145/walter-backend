import json
import datetime as dt

EVENT = json.load(open("tst/events/data/event.json"))


def get_walter_backend_event(email: str) -> dict:
    EVENT["Records"][0]["body"] = json.dumps({"email": email})
    return EVENT


def get_create_news_summary_and_archive_event(stock: str) -> dict:
    datestamp = dt.datetime.now().strftime("%Y-%m-%d")
    EVENT["Records"][0]["body"] = json.dumps(
        {"datestamp": datestamp, "stock": stock.upper()}
    )
    return EVENT
