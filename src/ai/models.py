from dataclasses import dataclass


@dataclass
class Prompt:
    name: str
    prompt: str
    max_gen_len: float


@dataclass
class Response:
    name: str
    response: str
