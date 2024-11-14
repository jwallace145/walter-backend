import json

EVENT = json.load(open("tst/events/data/event.json"))


def get_walter_backend_event(email: str) -> dict:
    EVENT["Records"][0]["body"] = json.dumps({"email": email})
    return EVENT
