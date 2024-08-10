from dataclasses import dataclass


@dataclass
class Parameter:
    key: str
    prompt: str


@dataclass
class Response:
    key: str
    response: str
